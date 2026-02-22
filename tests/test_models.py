"""Tests for data models."""

from notes_vault.models import Consumer, FileGroup


def test_file_group():
    """Test FileGroup model."""
    fg = FileGroup(name="notes", path="/path/**/*.md")
    assert fg.name == "notes"
    assert fg.path == "/path/**/*.md"


def test_consumer():
    """Test Consumer model."""
    consumer = Consumer(
        name="claude",
        target="~/exports/claude",
        include_queries=[r"#public", r"#work"],
        exclude_queries=[r"#draft"],
        exclude_paths=["*private*"],
        rename=True,
    )
    assert consumer.name == "claude"
    assert consumer.target == "~/exports/claude"
    assert r"#public" in consumer.include_queries
    assert r"#draft" in consumer.exclude_queries
    assert "*private*" in consumer.exclude_paths
    assert consumer.rename is True


def test_consumer_defaults():
    """Test Consumer model defaults."""
    consumer = Consumer(name="test", target="/tmp/test")
    assert consumer.include_queries == []
    assert consumer.exclude_queries == []
    assert consumer.exclude_paths == []
    assert consumer.rename is False
