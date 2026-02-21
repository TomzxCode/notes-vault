"""Configuration management for notes-vault."""

import os
from pathlib import Path

import yaml

from notes_vault.models import ApiKey, Config, FileGroup, SensitivityLevel

APP_NAME = "notes-vault"


def get_config_dir() -> Path:
    """Get the XDG config directory path (~/.config/notes-vault by default)."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return base / APP_NAME


def get_data_dir() -> Path:
    """Get the XDG data directory path (~/.local/share/notes-vault by default)."""
    xdg_data_home = os.environ.get("XDG_DATA_HOME", "")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / APP_NAME


def get_config_path() -> Path:
    """Get the config.yaml file path."""
    return get_config_dir() / "config.yaml"


def get_db_path() -> Path:
    """Get the index.db file path."""
    return get_data_dir() / "index.db"


def get_log_path() -> Path:
    """Get the access.log file path."""
    return get_data_dir() / "access.log"


def load_config() -> Config:
    """Load configuration from YAML file."""
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Parse YAML structure into Pydantic models
    config = Config()

    # Load defaults
    if "defaults" in data:
        config.defaults = data["defaults"]

    # Load file groups
    if "files" in data:
        for name, file_data in data["files"].items():
            config.files[name] = FileGroup(name=name, **file_data)

    # Load API keys
    if "keys" in data:
        for name, key_data in data["keys"].items():
            config.keys[name] = ApiKey(key_name=name, **key_data)

    # Load sensitivity levels
    if "sensitivities" in data:
        for name, sens_data in data["sensitivities"].items():
            config.sensitivities[name] = SensitivityLevel(name=name, **sens_data)

    return config


def save_config(config: Config) -> None:
    """Save configuration to YAML file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()

    # Convert Pydantic models to dict structure
    data = {
        "defaults": config.defaults,
        "files": {
            name: {"path": fg.path, "sensitivity": fg.sensitivity}
            for name, fg in config.files.items()
        },
        "keys": {
            name: {"key_hash": key.key_hash, "sensitivities": sorted(list(key.sensitivities))}
            for name, key in config.keys.items()
        },
        "sensitivities": {
            name: {
                "description": sens.description,
                "query": sens.query,
                "includes": sorted(list(sens.includes)),
            }
            for name, sens in config.sensitivities.items()
        },
    }

    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
