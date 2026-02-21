"""Tests for configuration management."""

from notes_vault.config import load_config, save_config


def test_load_config_empty(temp_config_dir):
    """Test loading config when file doesn't exist."""
    config = load_config()
    assert config is not None
    assert len(config.files) == 0
    assert len(config.keys) == 0
    assert len(config.sensitivities) == 0


def test_save_and_load_config(temp_config_dir, sample_config):
    """Test saving and loading configuration."""
    # Save config
    save_config(sample_config)

    # Load it back
    loaded_config = load_config()

    assert len(loaded_config.files) == 1
    assert "mynotes" in loaded_config.files
    assert loaded_config.files["mynotes"].sensitivity == "private"

    assert len(loaded_config.keys) == 3
    assert "admin_key" in loaded_config.keys
    assert "private" in loaded_config.keys["admin_key"].sensitivities

    assert len(loaded_config.sensitivities) == 3
    assert "private" in loaded_config.sensitivities
    assert "public" in loaded_config.sensitivities["private"].includes


def test_config_defaults(temp_config_dir, sample_config):
    """Test default configuration values."""
    save_config(sample_config)
    loaded_config = load_config()

    assert "sensitivity" in loaded_config.defaults
    assert loaded_config.defaults["sensitivity"] == "private"
