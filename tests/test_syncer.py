"""Tests for file sync logic."""

from pathlib import Path

from notes_vault.models import Consumer
from notes_vault.syncer import sync_all, sync_consumer


def test_sync_exports_matching_files(temp_notes_dir, sample_config):
    """Test that sync exports files matching a consumer's include_queries."""
    consumer = sample_config.consumers["public"]
    stats = sync_consumer("public", consumer, sample_config)

    assert stats["errors"] == 0
    target = Path(consumer.target)
    exported = {f.name for f in target.glob("*.md")}

    assert "public.md" in exported
    assert "mixed.md" in exported
    assert "draft.md" in exported


def test_sync_skips_non_matching_files(temp_notes_dir, sample_config):
    """Test that files without a matching include_query are not exported."""
    consumer = sample_config.consumers["public"]
    sync_consumer("public", consumer, sample_config)

    exported = {f.name for f in Path(consumer.target).glob("*.md")}
    assert "private.md" not in exported
    assert "work.md" not in exported


def test_sync_exclude_query_prevents_export(temp_notes_dir, sample_config):
    """Test that a matching exclude_query prevents export even if include matches."""
    consumer = sample_config.consumers["no_drafts"]
    sync_consumer("no_drafts", consumer, sample_config)

    exported = {f.name for f in Path(consumer.target).glob("*.md")}
    assert "public.md" in exported
    assert "mixed.md" in exported
    assert "draft.md" not in exported


def test_sync_multiple_include_queries(temp_notes_dir, sample_config):
    """Test that any matching include_query is sufficient for export."""
    consumer = sample_config.consumers["work"]
    sync_consumer("work", consumer, sample_config)

    exported = {f.name for f in Path(consumer.target).glob("*.md")}
    assert "work.md" in exported
    assert "private.md" in exported
    assert "mixed.md" in exported


def test_sync_no_include_queries_exports_nothing(temp_notes_dir, temp_export_dir, sample_config):
    """Test that a consumer with no include_queries exports nothing."""
    consumer = Consumer(
        name="empty",
        target=str(temp_export_dir / "empty"),
        include_queries=[],
        exclude_queries=[],
        exclude_paths=[],
        rename=False,
    )
    stats = sync_consumer("empty", consumer, sample_config)

    assert stats["exported"] == 0
    assert stats["errors"] == 0


def test_sync_rename_uses_uuid_filenames(temp_dir, temp_notes_dir, sample_config):
    """Test that rename=True exports files with UUID filenames."""
    consumer = Consumer(
        name="renamed",
        target=str(temp_dir / "renamed"),
        include_queries=[r"#public"],
        exclude_queries=[],
        exclude_paths=[],
        rename=True,
    )
    sync_consumer("renamed", consumer, sample_config)

    exported = list(Path(consumer.target).glob("*.md"))
    assert len(exported) == 3  # public.md, mixed.md, draft.md

    for f in exported:
        assert f.stem not in ("public", "mixed", "draft")
        assert len(f.stem) == 36  # UUID format


def test_sync_recreates_target_directory(temp_notes_dir, sample_config):
    """Test that sync deletes and recreates the target directory."""
    consumer = sample_config.consumers["public"]
    target = Path(consumer.target)
    target.mkdir(parents=True, exist_ok=True)

    stale = target / "stale.md"
    stale.write_text("stale content")

    sync_consumer("public", consumer, sample_config)

    assert not stale.exists()


def test_sync_all(temp_config_dir, temp_notes_dir, sample_config):
    """Test syncing all consumers."""
    from notes_vault.config import save_config

    save_config(sample_config)
    results = sync_all()

    assert "public" in results
    assert "work" in results
    assert "no_drafts" in results
    for stats in results.values():
        assert stats["errors"] == 0


def test_sync_specific_consumer(temp_config_dir, temp_notes_dir, sample_config):
    """Test syncing a specific consumer."""
    from notes_vault.config import save_config

    save_config(sample_config)
    results = sync_all("public")

    assert "public" in results
    assert "work" not in results
    assert "no_drafts" not in results


def test_sync_exclude_paths_prevents_export(temp_notes_dir, temp_export_dir, sample_config):
    """Test that exclude_paths prevents export based on glob patterns."""
    consumer = Consumer(
        name="no_private_files",
        target=str(temp_export_dir / "filtered"),
        include_queries=[r"#public", r"#private"],
        exclude_queries=[],
        exclude_paths=["*private*"],
        rename=False,
    )
    sync_consumer("no_private_files", consumer, sample_config)

    exported = {f.name for f in Path(consumer.target).glob("*.md")}
    assert "public.md" in exported
    assert "mixed.md" in exported
    assert "draft.md" in exported
    assert "private.md" not in exported


def test_sync_exclude_paths_with_extension(temp_notes_dir, temp_export_dir, sample_config):
    """Test that exclude_paths filters by file extension."""
    consumer = Consumer(
        name="markdown_only",
        target=str(temp_export_dir / "md_only"),
        include_queries=[r"."],  # Match everything
        exclude_queries=[],
        exclude_paths=["*.txt"],
        rename=False,
    )
    sync_consumer("markdown_only", consumer, sample_config)

    exported = {f.name for f in Path(consumer.target).glob("*")}
    assert "public.md" in exported
    assert len([f for f in Path(consumer.target).glob("*.txt")]) == 0


def test_sync_preserves_directory_structure_when_rename_false(temp_dir, sample_config):
    """Test that rename=False preserves source directory structure."""
    # Create notes with nested structure
    notes_dir = temp_dir / "nested_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    subdir = notes_dir / "subdir"
    subdir.mkdir(parents=True, exist_ok=True)

    (notes_dir / "root.md").write_text("Root #public content")
    (subdir / "nested.md").write_text("Nested #public content")

    # Update config to use the nested notes
    from notes_vault.models import FileGroup
    from notes_vault.syncer import sync_consumer

    sample_config.files = {"nested": FileGroup(name="nested", path=f"{notes_dir}/**/*.md")}

    consumer = Consumer(
        name="structured",
        target=str(temp_dir / "structured_export"),
        include_queries=[r"#public"],
        exclude_queries=[],
        exclude_paths=[],
        rename=False,
    )
    sync_consumer("structured", consumer, sample_config)

    target = Path(consumer.target)

    # Files should be in their original subdirectory structure
    assert (target / "root.md").exists()
    assert (target / "subdir" / "nested.md").exists()

    # Verify content
    assert (target / "root.md").read_text() == "Root #public content"
    assert (target / "subdir" / "nested.md").read_text() == "Nested #public content"
