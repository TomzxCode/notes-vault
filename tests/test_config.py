"""Tests for configuration management."""

from notes_vault.config import load_config, save_config


def test_load_config_empty(temp_config_dir):
    """Test loading config when file doesn't exist."""
    config = load_config()
    assert config is not None
    assert len(config.files) == 0
    assert len(config.consumers) == 0


def test_save_and_load_config(temp_config_dir, sample_config):
    """Test saving and loading configuration."""
    save_config(sample_config)

    loaded = load_config()

    assert len(loaded.files) == 1
    assert "mynotes" in loaded.files

    assert len(loaded.consumers) == 3
    assert "public" in loaded.consumers
    assert r"#public" in loaded.consumers["public"].include_queries

    assert "no_drafts" in loaded.consumers
    assert r"#draft" in loaded.consumers["no_drafts"].exclude_queries
