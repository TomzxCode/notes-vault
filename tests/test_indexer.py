"""Tests for file indexing logic."""

from notes_vault.config import save_config
from notes_vault.indexer import index_all
from notes_vault.storage import init_db, list_notes


def test_index_all(temp_config_dir, temp_notes_dir, sample_config):
    """Test indexing all files."""
    init_db()
    save_config(sample_config)

    stats = index_all()

    assert stats["indexed"] > 0
    assert stats["errors"] == 0

    # Verify notes were indexed
    notes = list_notes()
    assert len(notes) > 0


def test_index_detects_sensitivities(temp_config_dir, temp_notes_dir, sample_config):
    """Test that indexing correctly detects sensitivities."""
    init_db()
    save_config(sample_config)

    index_all()

    notes = list_notes()

    # Find the private note
    private_note = next((n for n in notes if "private.md" in n.file_path), None)
    assert private_note is not None
    assert private_note.effective_sensitivity == "private"

    # Find the public note
    public_note = next((n for n in notes if "public.md" in n.file_path), None)
    assert public_note is not None
    assert public_note.effective_sensitivity == "public"


def test_index_mixed_tags(temp_config_dir, temp_notes_dir, sample_config):
    """Test indexing file with multiple tags."""
    init_db()
    save_config(sample_config)

    index_all()

    notes = list_notes()

    # Find the mixed note
    mixed_note = next((n for n in notes if "mixed.md" in n.file_path), None)
    assert mixed_note is not None
    assert "public" in mixed_note.detected_sensitivities
    assert "private" in mixed_note.detected_sensitivities
    # Should use precedence (private > public)
    assert mixed_note.effective_sensitivity == "private"


def test_index_no_tags(temp_config_dir, temp_notes_dir, sample_config):
    """Test indexing file with no tags uses file group default."""
    init_db()
    save_config(sample_config)

    index_all()

    notes = list_notes()

    # Find the no_tags note
    no_tags_note = next((n for n in notes if "no_tags.md" in n.file_path), None)
    assert no_tags_note is not None
    assert len(no_tags_note.detected_sensitivities) == 0
    # Should use file group default
    assert no_tags_note.effective_sensitivity == "private"


def test_index_incremental(temp_config_dir, temp_notes_dir, sample_config):
    """Test that re-indexing skips unchanged files."""
    init_db()
    save_config(sample_config)

    # First indexing
    stats1 = index_all()
    indexed_count1 = stats1["indexed"]

    # Second indexing (nothing changed)
    stats2 = index_all()
    assert stats2["indexed"] == 0  # Should skip all files
    assert stats2["skipped"] == indexed_count1
