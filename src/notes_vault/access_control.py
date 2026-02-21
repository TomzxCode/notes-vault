"""Access control and permission checking."""

import hashlib
from datetime import datetime
from uuid import UUID

import structlog

from notes_vault.config import load_config
from notes_vault.models import AccessLogEntry, ApiKey, NoteMetadata
from notes_vault.sensitivity import expand_access
from notes_vault.storage import get_note_by_uuid, list_notes, log_access

logger = structlog.get_logger()


def resolve_key(raw_key: str) -> ApiKey | None:
    """
    Find an ApiKey by its raw secret value.

    Hashes the provided key and compares against stored hashes.

    Args:
        raw_key: The raw secret key provided by the caller

    Returns:
        The matching ApiKey if found, None otherwise
    """
    config = load_config()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    for api_key in config.keys.values():
        if api_key.key_hash == key_hash:
            return api_key
    return None


def check_access(api_key_name: str, note: NoteMetadata) -> bool:
    """
    Check if an API key has access to a note.

    Args:
        api_key_name: Name of the API key
        note: Note metadata to check access for

    Returns:
        True if access is granted
    """
    config = load_config()

    # Get API key
    if api_key_name not in config.keys:
        logger.warning("API key not found", api_key=api_key_name)
        return False

    api_key = config.keys[api_key_name]

    # Expand access using includes
    accessible_sensitivities = expand_access(api_key.sensitivities, config)

    # Check if note's effective sensitivity is accessible
    return note.effective_sensitivity in accessible_sensitivities


def get_accessible_notes(api_key_name: str) -> list[NoteMetadata]:
    """
    Get all notes accessible by an API key.

    Args:
        api_key_name: Name of the API key

    Returns:
        List of accessible note metadata
    """
    config = load_config()

    # Get API key
    if api_key_name not in config.keys:
        logger.warning("API key not found", api_key=api_key_name)
        log_access(
            AccessLogEntry(
                timestamp=datetime.now(),
                api_key=api_key_name,
                action="list",
                granted=False,
            )
        )
        return []

    api_key = config.keys[api_key_name]

    # Expand access using includes
    accessible_sensitivities = expand_access(api_key.sensitivities, config)

    # Log access
    log_access(
        AccessLogEntry(
            timestamp=datetime.now(),
            api_key=api_key_name,
            action="list",
            granted=True,
        )
    )

    # Get all notes with accessible sensitivities
    return list_notes(accessible_sensitivities)


def get_note_if_accessible(api_key_name: str, note_uuid: UUID) -> NoteMetadata | None:
    """
    Get a note by UUID if accessible by the API key.

    Args:
        api_key_name: Name of the API key
        note_uuid: UUID of the note to retrieve

    Returns:
        Note metadata if accessible, None otherwise
    """
    note = get_note_by_uuid(note_uuid)
    if not note:
        logger.warning("Note not found", uuid=str(note_uuid))
        log_access(
            AccessLogEntry(
                timestamp=datetime.now(),
                api_key=api_key_name,
                action="get",
                note_uuid=note_uuid,
                granted=False,
            )
        )
        return None

    granted = check_access(api_key_name, note)

    # Log access attempt
    log_access(
        AccessLogEntry(
            timestamp=datetime.now(),
            api_key=api_key_name,
            action="get",
            note_uuid=note_uuid,
            granted=granted,
        )
    )

    if granted:
        return note
    else:
        logger.warning(
            "Access denied",
            api_key=api_key_name,
            uuid=str(note_uuid),
            sensitivity=note.effective_sensitivity,
        )
        return None
