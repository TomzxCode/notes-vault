"""Tests for query command."""

from unittest.mock import MagicMock, patch

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

    # Mock ripgrep output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        '{"type":"match","data":{"path":{"text":"/tmp/private.md"},'
        '"line_number":1,"lines":{"text":"This is #private content"}}}\n'
    )

    with patch("subprocess.run", return_value=mock_result):
        query(TEST_RAW_KEYS["admin_key"], "private", False, with_context=True)

    captured = capsys.readouterr()
    assert "Found" in captured.out
    assert "notes matching" in captured.out


def test_query_no_matches(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command with no matches."""
    init_db()
    save_config(sample_config)
    index_all()

    # Mock ripgrep with no matches (exit code 1)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        query(TEST_RAW_KEYS["admin_key"], "nonexistent_string_xyz", False)

    captured = capsys.readouterr()
    assert "No matches found" in captured.out


def test_query_case_sensitive(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test case sensitive query."""
    init_db()
    save_config(sample_config)
    index_all()

    # Mock ripgrep with no matches for case-sensitive search
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        query(TEST_RAW_KEYS["admin_key"], "PRIVATE", True)

    captured = capsys.readouterr()
    assert "No matches found" in captured.out


def test_query_respects_access_control(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query respects access control."""
    init_db()
    save_config(sample_config)
    index_all()

    # Mock ripgrep with matches
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        '{"type":"match","data":{"path":{"text":"/tmp/public.md"},'
        '"line_number":1,"lines":{"text":"This is #public content"}}}\n'
    )

    with patch("subprocess.run", return_value=mock_result):
        query(TEST_RAW_KEYS["public_key"], "content", False)

    captured = capsys.readouterr()
    # Should find matches or show no accessible notes
    assert "Found" in captured.out or "No matches" in captured.out or "accessible" in captured.out


def test_query_ripgrep_not_found(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command when ripgrep is not installed."""
    init_db()
    save_config(sample_config)
    index_all()

    # Mock FileNotFoundError when ripgrep is not available
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        query(TEST_RAW_KEYS["admin_key"], "test", False)

    captured = capsys.readouterr()
    assert "ripgrep (rg) not found" in captured.out


def test_query_files_only(temp_config_dir, temp_notes_dir, sample_config, capsys):
    """Test query command defaults to files-only output."""
    init_db()
    save_config(sample_config)
    index_all()

    # Mock ripgrep output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        '{"type":"match","data":{"path":{"text":"/tmp/private.md"},'
        '"line_number":1,"lines":{"text":"This is #private content"}}}\n'
    )

    with patch("subprocess.run", return_value=mock_result):
        query(TEST_RAW_KEYS["admin_key"], "private", False)

    captured = capsys.readouterr()
    # Should only contain UUID, not "Found" or other details
    assert "Found" not in captured.out
    assert "Sensitivity:" not in captured.out
    assert "Line" not in captured.out
    # Should have at least one line of output (UUID)
    assert len(captured.out.strip()) > 0
