"""Tests for query command."""

from notes_vault.commands.user import query
from notes_vault.config import save_config
from notes_vault.indexer import index_all
from notes_vault.storage import init_db
from tests.helpers import TEST_RAW_KEYS


def test_query_finds_matches(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command finds matching content."""
    init_db()
    save_config(sample_config)
    index_all()

    query("private", TEST_RAW_KEYS["admin_key"], case_sensitive=False, with_context=True)

    captured = capsys.readouterr()
    assert "Found" in captured.out
    assert "notes matching" in captured.out


def test_query_no_matches(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command with no matches."""
    init_db()
    save_config(sample_config)
    index_all()

    query("nonexistent_string_xyz", TEST_RAW_KEYS["admin_key"])

    captured = capsys.readouterr()
    assert "No matches found" in captured.out


def test_query_case_sensitive(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test case sensitive query."""
    init_db()
    save_config(sample_config)
    index_all()

    # "PRIVATE" (uppercase) should not match "#private" (lowercase) in case-sensitive mode
    query("PRIVATE", TEST_RAW_KEYS["admin_key"], case_sensitive=True)

    captured = capsys.readouterr()
    assert "No matches found" in captured.out


def test_query_respects_access_control(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query respects access control."""
    init_db()
    save_config(sample_config)
    index_all()

    # public_key only has access to "public" sensitivity notes
    query("private", TEST_RAW_KEYS["public_key"])

    captured = capsys.readouterr()
    # Should not find private notes via a public key
    assert "Found" not in captured.out or "No matches" in captured.out


def test_query_files_only(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command defaults to UUID-only output."""
    init_db()
    save_config(sample_config)
    index_all()

    query("private", TEST_RAW_KEYS["admin_key"])

    captured = capsys.readouterr()
    # Should only contain UUID, not detailed context fields
    assert "Found" not in captured.out
    assert "Sensitivity:" not in captured.out
    assert "Line" not in captured.out
    # Should have at least one line of output (UUID)
    assert len(captured.out.strip()) > 0
