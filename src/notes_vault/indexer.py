"""File discovery and indexing logic."""

import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import structlog

from notes_vault.config import load_config
from notes_vault.models import Config, NoteMetadata
from notes_vault.sensitivity import detect_sensitivities
from notes_vault.storage import delete_note_by_path, init_db, list_notes, upsert_notes_batch

logger = structlog.get_logger()


def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def should_reindex(file_path: Path, existing_note: NoteMetadata | None) -> bool:
    """
    Determine if a file should be re-indexed.

    Args:
        file_path: Path to the file
        existing_note: Existing note metadata from database, if any

    Returns:
        True if file should be re-indexed
    """
    if not existing_note:
        return True

    # Check if file modification time is newer than last indexed time
    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return file_mtime > existing_note.last_indexed


def index_file(
    file_path: Path,
    file_group_name: str,
    file_group_sensitivity: str,
    config: Config,
    existing_note: NoteMetadata | None,
) -> tuple[NoteMetadata, str] | None:
    """
    Index a single file.

    Args:
        file_path: Path to the file to index
        file_group_name: Name of the file group
        file_group_sensitivity: Default sensitivity for the file group (used if no tags detected)
        config: Application configuration
        existing_note: Existing note metadata from database, if any

    Returns:
        (NoteMetadata, content) tuple if indexed successfully, None on read error
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to read file", file_path=str(file_path), error=str(e))
        return None

    # Detect sensitivities from content hashtags
    detected = detect_sensitivities(content, config)

    # If no sensitivities detected, use file group default
    if not detected:
        detected = {file_group_sensitivity}

    # Generate or reuse UUID
    note_uuid = existing_note.uuid if existing_note else uuid4()

    # Create metadata
    note = NoteMetadata(
        uuid=note_uuid,
        file_path=str(file_path),
        file_group=file_group_name,
        detected_sensitivities=detected,
        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
        last_indexed=datetime.now(),
        content_hash=calculate_content_hash(content),
    )

    logger.info(
        "Indexed file",
        file_path=str(file_path),
        uuid=str(note_uuid),
        detected_sensitivities=sorted(detected),
    )
    return note, content


def _collect_files(
    config: Config,
    on_file_found: Callable[[], None] | None = None,
) -> list[tuple[Path, str, str]]:
    """Collect all files from configured file groups, returning (path, group_name, sensitivity)."""
    result = []
    for file_group_name, file_group in config.files.items():
        logger.info("Scanning file group", group=file_group_name, pattern=file_group.path)
        pattern = Path(file_group.path).expanduser()
        if "**" in str(pattern):
            base_path = Path(str(pattern).split("**")[0])
            relative_pattern = str(pattern).replace(str(base_path), "").lstrip("/")
            files = base_path.glob(relative_pattern)
        else:
            files = Path().glob(str(pattern))
        for file_path in files:
            if file_path.is_file():
                result.append((file_path, file_group_name, file_group.sensitivity))
                if on_file_found:
                    on_file_found()
    return result


def index_all(
    progress_callback: Callable[[int, int], None] | None = None,
    on_file_found: Callable[[], None] | None = None,
) -> dict[str, int]:
    """
    Index all files from configured file groups.

    Args:
        progress_callback: Optional callback called with (current, total) after each file.

    Returns:
        Dictionary with statistics: indexed, skipped, errors
    """
    config = load_config()
    init_db()

    stats = {"indexed": 0, "skipped": 0, "errors": 0}
    indexed_paths: set[str] = set()
    notes_to_upsert: list[tuple[NoteMetadata, str]] = []

    # Load all existing notes upfront (one DB query instead of one per file)
    existing_notes = {n.file_path: n for n in list_notes()}

    # Collect all files first so we know the total for progress reporting
    all_files = _collect_files(config, on_file_found=on_file_found)
    total = len(all_files)

    for current, (file_path, file_group_name, file_group_sensitivity) in enumerate(
        all_files, start=1
    ):
        path_str = str(file_path)
        indexed_paths.add(path_str)
        existing_note = existing_notes.get(path_str)

        try:
            if should_reindex(file_path, existing_note):
                result = index_file(
                    file_path, file_group_name, file_group_sensitivity, config, existing_note
                )
                if result is None:
                    stats["errors"] += 1
                else:
                    notes_to_upsert.append(result)
                    stats["indexed"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            logger.error("Failed to index file", file_path=str(file_path), error=str(e))
            stats["errors"] += 1

        if progress_callback:
            progress_callback(current, total)

    # Batch upsert all indexed notes in a single transaction
    upsert_notes_batch(notes_to_upsert)

    # Remove deleted files from index
    for note in existing_notes.values():
        if note.file_path not in indexed_paths and not Path(note.file_path).exists():
            logger.info("Removing deleted file from index", file_path=note.file_path)
            delete_note_by_path(note.file_path)

    return stats
