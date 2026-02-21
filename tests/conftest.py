"""Pytest fixtures for notes-vault tests."""

import hashlib
import tempfile
from pathlib import Path

import pytest

from notes_vault.models import ApiKey, Config, FileGroup, SensitivityLevel
from tests.helpers import TEST_RAW_KEYS


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_dir(temp_dir, monkeypatch, worker_id="master"):
    """Set up a temporary config directory."""
    config_dir = temp_dir / ".vault"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("notes_vault.config.get_config_dir", lambda: config_dir)

    # Also patch get_data_dir to use worker-specific path for xdist isolation
    data_dir = temp_dir / ".data"
    if worker_id != "master":
        data_dir = temp_dir / f".data_{worker_id}"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("notes_vault.config.get_data_dir", lambda: data_dir)

    return config_dir


@pytest.fixture
def temp_notes_dir(temp_dir):
    """Create a temporary notes directory with sample files."""
    notes_dir = temp_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    # Create sample notes
    (notes_dir / "private.md").write_text("This is #private content")
    (notes_dir / "public.md").write_text("This is #public content")
    (notes_dir / "work.md").write_text("This is #work related content")
    (notes_dir / "mixed.md").write_text("This has #public and #private tags")
    (notes_dir / "no_tags.md").write_text("This has no tags at all")

    return notes_dir


@pytest.fixture
def sample_config(temp_notes_dir):
    """Create a sample configuration."""
    config = Config()

    # Set defaults
    config.defaults = {"sensitivity": "private"}

    # Add file groups
    config.files = {
        "mynotes": FileGroup(
            name="mynotes",
            path=f"{temp_notes_dir}/**/*.md",
            sensitivity="private",
        )
    }

    # Add sensitivity levels
    config.sensitivities = {
        "private": SensitivityLevel(
            name="private",
            description="Private notes",
            query=r"#private",
            includes={"work", "public"},
        ),
        "work": SensitivityLevel(
            name="work",
            description="Work notes",
            query=r"#work",
            includes={"public"},
        ),
        "public": SensitivityLevel(
            name="public",
            description="Public notes",
            query=r"#public",
            includes=set(),
        ),
    }

    # Add API keys (key_hash is SHA-256 of the corresponding TEST_RAW_KEYS value)
    config.keys = {
        name: ApiKey(
            key_name=name,
            key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
            sensitivities=sensitivities,
        )
        for name, raw_key, sensitivities in [
            ("admin_key", TEST_RAW_KEYS["admin_key"], {"private"}),
            ("work_key", TEST_RAW_KEYS["work_key"], {"work"}),
            ("public_key", TEST_RAW_KEYS["public_key"], {"public"}),
        ]
    }

    return config
