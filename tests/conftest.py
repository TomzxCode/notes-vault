"""Pytest fixtures for notes-vault tests."""

import tempfile
from pathlib import Path

import pytest

from notes_vault.models import Config, Consumer, FileGroup


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_dir(temp_dir, monkeypatch):
    """Set up a temporary config directory."""
    config_dir = temp_dir / ".vault"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("notes_vault.config.get_config_dir", lambda: config_dir)
    return config_dir


@pytest.fixture
def temp_notes_dir(temp_dir):
    """Create a temporary notes directory with sample files."""
    notes_dir = temp_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    (notes_dir / "private.md").write_text("This is #private content")
    (notes_dir / "public.md").write_text("This is #public content")
    (notes_dir / "work.md").write_text("This is #work related content")
    (notes_dir / "mixed.md").write_text("This has #public and #private tags")
    (notes_dir / "draft.md").write_text("This is a #public #draft")

    return notes_dir


@pytest.fixture
def temp_export_dir(temp_dir):
    """Create a temporary export directory."""
    export_dir = temp_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


@pytest.fixture
def sample_config(temp_notes_dir, temp_export_dir):
    """Create a sample configuration."""
    config = Config()

    config.files = {
        "mynotes": FileGroup(
            name="mynotes",
            path=f"{temp_notes_dir}/**/*.md",
        )
    }

    config.consumers = {
        "public": Consumer(
            name="public",
            target=str(temp_export_dir / "public"),
            include_queries=[r"#public"],
            exclude_queries=[],
            exclude_paths=[],
            rename=False,
        ),
        "work": Consumer(
            name="work",
            target=str(temp_export_dir / "work"),
            include_queries=[r"#work", r"#private"],
            exclude_queries=[],
            exclude_paths=[],
            rename=False,
        ),
        "no_drafts": Consumer(
            name="no_drafts",
            target=str(temp_export_dir / "no_drafts"),
            include_queries=[r"#public"],
            exclude_queries=[r"#draft"],
            exclude_paths=[],
            rename=False,
        ),
    }

    return config
