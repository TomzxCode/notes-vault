"""File discovery and indexing logic."""

import hashlib
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import structlog

from notes_vault.config import load_config
from notes_vault.models import Config, NoteMetadata
from notes_vault.sensitivity import detect_sensitivities, resolve_effective_sensitivity
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
) -> NoteMetadata | None:
    """
    Index a single file.

    Args:
        file_path: Path to the file to index
        file_group_name: Name of the file group
        file_group_sensitivity: Default sensitivity for the file group
        config: Application configuration
        existing_note: Existing note metadata from database, if any

    Returns:
        NoteMetadata if indexed successfully, None on read error
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to read file", file_path=str(file_path), error=str(e))
        return None

    # Detect sensitivities
    detected = detect_sensitivities(content, config)
    effective = resolve_effective_sensitivity(detected, file_group_sensitivity, config)

    # Generate or reuse UUID
    note_uuid = existing_note.uuid if existing_note else uuid4()

    # Create metadata
    note = NoteMetadata(
        uuid=note_uuid,
        file_path=str(file_path),
        file_group=file_group_name,
        detected_sensitivities=detected,
        effective_sensitivity=effective,
        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
        last_indexed=datetime.now(),
        content_hash=calculate_content_hash(content),
    )

    logger.info(
        "Indexed file",
        file_path=str(file_path),
        uuid=str(note_uuid),
        effective_sensitivity=effective,
    )
    return note


def index_all() -> dict[str, int]:
    """
    Index all files from configured file groups.

    Returns:
        Dictionary with statistics: indexed, skipped, errors
    """
    config = load_config()
    init_db()

    stats = {"indexed": 0, "skipped": 0, "errors": 0}
    indexed_paths: set[str] = set()
    notes_to_upsert: list[NoteMetadata] = []

    # Load all existing notes upfront (one DB query instead of one per file)
    existing_notes = {n.file_path: n for n in list_notes()}

    for file_group_name, file_group in config.files.items():
        logger.info("Indexing file group", group=file_group_name, pattern=file_group.path)

        # Expand glob pattern
        pattern = Path(file_group.path).expanduser()
        if "**" in str(pattern):
            # Handle recursive glob
            base_path = Path(str(pattern).split("**")[0])
            relative_pattern = str(pattern).replace(str(base_path), "").lstrip("/")
            files = base_path.glob(relative_pattern)
        else:
            files = Path().glob(str(pattern))

        for file_path in files:
            if not file_path.is_file():
                continue

            path_str = str(file_path)
            indexed_paths.add(path_str)
            existing_note = existing_notes.get(path_str)

            try:
                if should_reindex(file_path, existing_note):
                    note = index_file(
                        file_path, file_group_name, file_group.sensitivity, config, existing_note
                    )
                    if note is None:
                        stats["errors"] += 1
                    else:
                        notes_to_upsert.append(note)
                        stats["indexed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error("Failed to index file", file_path=str(file_path), error=str(e))
                stats["errors"] += 1

    # Batch upsert all indexed notes in a single transaction
    upsert_notes_batch(notes_to_upsert)

    # Remove deleted files from index
    for note in existing_notes.values():
        if note.file_path not in indexed_paths and not Path(note.file_path).exists():
            logger.info("Removing deleted file from index", file_path=note.file_path)
            delete_note_by_path(note.file_path)

    return stats
