"""Tests for SQLite storage layer."""

from datetime import datetime
from uuid import uuid4

from notes_vault.models import AccessLogEntry, NoteMetadata
from notes_vault.storage import (
    clear_all_notes,
    delete_note_by_path,
    get_note_by_path,
    get_note_by_uuid,
    init_db,
    list_notes,
    log_access,
    upsert_note,
)


def test_init_db(temp_config_dir):
    """Test database initialization."""
    init_db()
    # Should not raise any errors


def test_upsert_and_get_note(temp_config_dir):
    """Test inserting and retrieving a note."""
    init_db()

    note_uuid = uuid4()
    note = NoteMetadata(
        uuid=note_uuid,
        file_path="/test/note.md",
        file_group="notes",
        detected_sensitivities={"private"},
        effective_sensitivity="private",
        last_modified=datetime.now(),
        last_indexed=datetime.now(),
        content_hash="abc123",
    )

    upsert_note(note)

    # Retrieve by UUID
    retrieved = get_note_by_uuid(note_uuid)
    assert retrieved is not None
    assert retrieved.uuid == note_uuid
    assert retrieved.effective_sensitivity == "private"

    # Retrieve by path
    retrieved_by_path = get_note_by_path("/test/note.md")
    assert retrieved_by_path is not None
    assert retrieved_by_path.uuid == note_uuid


def test_list_notes_filtered(temp_config_dir):
    """Test listing notes filtered by sensitivity."""
    init_db()
    clear_all_notes()

    # Create notes with different sensitivities
    for i, sensitivity in enumerate(["private", "public", "work"]):
        note = NoteMetadata(
            uuid=uuid4(),
            file_path=f"/test/note{i}.md",
            file_group="notes",
            detected_sensitivities={sensitivity},
            effective_sensitivity=sensitivity,
            last_modified=datetime.now(),
            last_indexed=datetime.now(),
            content_hash=f"hash{i}",
        )
        upsert_note(note)

    # List all notes
    all_notes = list_notes()
    assert len(all_notes) == 3

    # List only public notes
    public_notes = list_notes({"public"})
    assert len(public_notes) == 1
    assert public_notes[0].effective_sensitivity == "public"


def test_delete_note(temp_config_dir):
    """Test deleting a note."""
    init_db()

    note = NoteMetadata(
        uuid=uuid4(),
        file_path="/test/delete.md",
        file_group="notes",
        detected_sensitivities=set(),
        effective_sensitivity="private",
        last_modified=datetime.now(),
        last_indexed=datetime.now(),
        content_hash="abc",
    )
    upsert_note(note)

    # Verify it exists
    assert get_note_by_path("/test/delete.md") is not None

    # Delete it
    delete_note_by_path("/test/delete.md")

    # Verify it's gone
    assert get_note_by_path("/test/delete.md") is None


def test_log_access(temp_config_dir):
    """Test logging access attempts."""
    init_db()

    entry = AccessLogEntry(
        timestamp=datetime.now(),
        api_key="test_key",
        action="get",
        note_uuid=uuid4(),
        granted=True,
    )

    log_access(entry)
    # Should not raise any errors
