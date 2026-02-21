"""Tests for sensitivity detection logic."""

from notes_vault.sensitivity import (
    detect_sensitivities,
    expand_access,
)


def test_detect_sensitivities(sample_config):
    """Test hashtag detection in content."""
    content = "This is a #private note"
    detected = detect_sensitivities(content, sample_config)
    assert "private" in detected


def test_detect_multiple_sensitivities(sample_config):
    """Test detection of multiple hashtags."""
    content = "This has #public and #private tags"
    detected = detect_sensitivities(content, sample_config)
    assert "public" in detected
    assert "private" in detected
    assert len(detected) == 2


def test_detect_no_sensitivities(sample_config):
    """Test content with no hashtags."""
    content = "This has no tags"
    detected = detect_sensitivities(content, sample_config)
    assert len(detected) == 0


def test_expand_access_no_includes(sample_config):
    """Test access expansion with no includes."""
    expanded = expand_access({"public"}, sample_config)
    assert expanded == {"public"}


def test_expand_access_with_includes(sample_config):
    """Test access expansion with includes."""
    expanded = expand_access({"private"}, sample_config)
    assert "private" in expanded
    assert "work" in expanded
    assert "public" in expanded
    assert len(expanded) == 3


def test_expand_access_work_key(sample_config):
    """Test work key expands to include public."""
    expanded = expand_access({"work"}, sample_config)
    assert "work" in expanded
    assert "public" in expanded
    assert "private" not in expanded
