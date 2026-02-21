"""Tests for data models."""

from datetime import datetime
from uuid import uuid4

from notes_vault.models import ApiKey, FileGroup, NoteMetadata, SensitivityLevel


def test_sensitivity_level():
    """Test SensitivityLevel model."""
    sens = SensitivityLevel(
        name="private",
        description="Private notes",
        query=r"#private",
        includes={"public", "friends"},
    )
    assert sens.name == "private"
    assert "public" in sens.includes
    assert len(sens.includes) == 2


def test_file_group():
    """Test FileGroup model."""
    fg = FileGroup(name="notes", path="/path/**/*.md", sensitivity="private")
    assert fg.name == "notes"
    assert fg.path == "/path/**/*.md"
    assert fg.sensitivity == "private"


def test_api_key():
    """Test ApiKey model."""
    key = ApiKey(key_name="test_key", key_hash="abc123", sensitivities={"public", "private"})
    assert key.key_name == "test_key"
    assert key.key_hash == "abc123"
    assert len(key.sensitivities) == 2
    assert "public" in key.sensitivities


def test_note_metadata():
    """Test NoteMetadata model."""
    note_uuid = uuid4()
    note = NoteMetadata(
        uuid=note_uuid,
        file_path="/test/note.md",
        file_group="notes",
        detected_sensitivities={"private", "public"},
        effective_sensitivity="private",
        last_modified=datetime.now(),
        last_indexed=datetime.now(),
        content_hash="abc123",
    )
    assert note.uuid == note_uuid
    assert note.effective_sensitivity == "private"
    assert len(note.detected_sensitivities) == 2
