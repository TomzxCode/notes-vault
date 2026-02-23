"""Configuration management for notes-vault."""

import os
from pathlib import Path

import yaml

from notes_vault.models import Config, Consumer, FileGroup

APP_NAME = "notes-vault"


def get_config_dir() -> Path:
    """Get the XDG config directory path (~/.config/notes-vault by default)."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return base / APP_NAME


def get_config_path() -> Path:
    """Get the config.yaml file path."""
    return get_config_dir() / "config.yaml"


def load_config() -> Config:
    """Load configuration from YAML file."""
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    config = Config()

    if "files" in data:
        for name, file_data in data["files"].items():
            config.files[name] = FileGroup(name=name, **file_data)

    if "consumers" in data:
        for name, consumer_data in data["consumers"].items():
            config.consumers[name] = Consumer(name=name, **consumer_data)

    return config


def save_config(config: Config) -> None:
    """Save configuration to YAML file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "files": {name: {"path": fg.path} for name, fg in config.files.items()},
        "consumers": {
            name: {
                "target": consumer.target,
                "include_queries": consumer.include_queries,
                "exclude_queries": consumer.exclude_queries,
                "rename": consumer.rename,
            }
            for name, consumer in config.consumers.items()
        },
    }

    with open(get_config_path(), "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
