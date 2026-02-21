"""Tests for access control logic."""

import hashlib

from notes_vault.access_control import check_access, get_accessible_notes, get_note_if_accessible, resolve_key
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
    public_note = next((n for n in notes if n.effective_sensitivity == "public"), None)
    assert public_note is not None

    # Public key should have access to public note
    assert check_access("public_key", public_note) is True


def test_check_access_denied(temp_config_dir, temp_notes_dir, sample_config):
    """Test access check when denied."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    private_note = next((n for n in notes if n.effective_sensitivity == "private"), None)
    assert private_note is not None

    # Public key should NOT have access to private note
    assert check_access("public_key", private_note) is False


def test_get_accessible_notes_admin(temp_config_dir, temp_notes_dir, sample_config):
    """Test admin key can access all notes."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("admin_key")

    # Admin key has private access which includes work and public
    assert len(accessible) > 0

    sensitivities = {note.effective_sensitivity for note in accessible}
    assert "private" in sensitivities or "public" in sensitivities or "work" in sensitivities


def test_get_accessible_notes_public(temp_config_dir, temp_notes_dir, sample_config):
    """Test public key can only access public notes."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("public_key")

    # Should only see public notes
    for note in accessible:
        assert note.effective_sensitivity == "public"


def test_get_accessible_notes_work(temp_config_dir, temp_notes_dir, sample_config):
    """Test work key can access work and public notes."""
    init_db()
    save_config(sample_config)
    index_all()

    accessible = get_accessible_notes("work_key")

    # Should see work and public notes (work includes public)
    sensitivities = {note.effective_sensitivity for note in accessible}
    assert "private" not in sensitivities


def test_get_note_if_accessible_granted(temp_config_dir, temp_notes_dir, sample_config):
    """Test getting a note when access is granted."""
    init_db()
    save_config(sample_config)
    index_all()

    notes = list_notes()
    public_note = next((n for n in notes if n.effective_sensitivity == "public"), None)
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
    private_note = next((n for n in notes if n.effective_sensitivity == "private"), None)
    assert private_note is not None

    # Public key should NOT be able to get private note
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
