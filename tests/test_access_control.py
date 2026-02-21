"""Tests for access control logic."""

import hashlib

from notes_vault.access_control import (
    check_access,
    get_accessible_notes,
    get_note_if_accessible,
    resolve_key,
)
from notes_vault.config import save_config
from notes_vault.indexer import index_all
from notes_vault.models import ApiKey
from notes_vault.storage import init_db, list_notes


def test_check_access_granted(temp_config_dir, temp_notes_dir, sample_config):
    """Test access check when granted."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    # Find a note with only public sensitivity
    public_note = next((n for n in notes if n.detected_sensitivities == {"public"}), None)
    assert public_note is not None

    # Public key should have access to public note
    assert check_access("public_key", public_note) is True


def test_check_access_denied(temp_config_dir, temp_notes_dir, sample_config):
    """Test access check when denied."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    # Find a note with only private sensitivity
    private_note = next((n for n in notes if n.detected_sensitivities == {"private"}), None)
    assert private_note is not None

    # Public key should NOT have access to private-only note
    assert check_access("public_key", private_note) is False


def test_check_access_union_based(temp_config_dir, temp_notes_dir, sample_config):
    """Test that union-based access works: a note with multiple tags is accessible to any matching key."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    # Find the mixed note with both public and private tags
    mixed_note = next((n for n in notes if "mixed" in n.file_path), None)
    assert mixed_note is not None
    assert "public" in mixed_note.detected_sensitivities
    assert "private" in mixed_note.detected_sensitivities

    # Public key should have access (via public tag)
    assert check_access("public_key", mixed_note) is True

    # Private/Admin key should have access (via private tag)
    assert check_access("admin_key", mixed_note) is True


def test_get_accessible_notes_admin(temp_config_dir, temp_notes_dir, sample_config):
    """Test admin key can access all notes."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("admin_key")

    # Admin key has private access, can see all notes in the test config
    assert len(accessible) > 0


def test_get_accessible_notes_public(temp_config_dir, temp_notes_dir, sample_config):
    """Test public key can access notes with public sensitivity (including mixed)."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("public_key")

    # Should see public-only notes and notes with public tag (like mixed)
    assert len(accessible) >= 2  # public.md and mixed.md

    # Check that all accessible notes have public in their detected sensitivities
    for note in accessible:
        assert "public" in note.detected_sensitivities


def test_get_accessible_notes_work(temp_config_dir, temp_notes_dir, sample_config):
    """Test work key can access work notes and notes with work tag."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("work_key")

    # Work key should see work.md and mixed.md (which has public, and work includes public)
    # But not private.md (only has private tag)
    assert len(accessible) >= 2

    # Check that accessible notes have work or public tags
    for note in accessible:
        assert "work" in note.detected_sensitivities or "public" in note.detected_sensitivities

    # Specifically, private-only notes should not be accessible
    private_only = next((n for n in accessible if n.detected_sensitivities == {"private"}), None)
    assert private_only is None


def test_get_note_if_accessible_granted(temp_config_dir, temp_notes_dir, sample_config):
    """Test getting a note when access is granted."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    public_note = next((n for n in notes if n.detected_sensitivities == {"public"}), None)
    assert public_note is not None

    # Public key should be able to get public note
    result = get_note_if_accessible("public_key", public_note.uuid)
    assert result is not None
    assert result.uuid == public_note.uuid


def test_get_note_if_accessible_denied(temp_config_dir, temp_notes_dir, sample_config):
    """Test getting a note when access is denied."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    private_note = next((n for n in notes if n.detected_sensitivities == {"private"}), None)
    assert private_note is not None

    # Public key should NOT be able to get private-only note
    result = get_note_if_accessible("public_key", private_note.uuid)
    assert result is None


def test_access_with_invalid_key(temp_config_dir, temp_notes_dir, sample_config):
    """Test access with invalid API key."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("invalid_key")
    assert len(accessible) == 0


def test_resolve_key_valid(temp_config_dir, sample_config):
    """Test that a raw key resolves to the correct ApiKey."""
    raw_key = "supersecretkey"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    sample_config.keys["hashed_key"] = ApiKey(
        key_name="hashed_key", key_hash=key_hash, sensitivities={"public"}
    )
    save_config(sample_config)

    result = resolve_key(raw_key)
    assert result is not None
    assert result.key_name == "hashed_key"


def test_resolve_key_invalid(temp_config_dir, sample_config):
    """Test that an unknown raw key returns None."""
    save_config(sample_config)

    result = resolve_key("doesnotexist")
    assert result is None
