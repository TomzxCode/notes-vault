"""Hashtag detection and sensitivity access logic."""

import re

from notes_vault.models import Config

_pattern_cache: dict[str, re.Pattern[str]] = {}


def detect_sensitivities(content: str, config: Config) -> set[str]:
    """
    Scan content for hashtags matching sensitivity query patterns.

    Args:
        content: The note content to scan
        config: Application configuration containing sensitivity definitions

    Returns:
        Set of detected sensitivity level names
    """
    detected = set()

    for name, sensitivity in config.sensitivities.items():
        pattern = sensitivity.query
        if pattern not in _pattern_cache:
            _pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)
        if _pattern_cache[pattern].search(content):
            detected.add(name)

    return detected


def expand_access(api_key_sensitivities: set[str], config: Config) -> set[str]:
    """
    Expand API key access to include all levels via 'includes' relationships.

    Args:
        api_key_sensitivities: Direct sensitivity levels from API key
        config: Application configuration with sensitivity definitions

    Returns:
        Expanded set of accessible sensitivity level names
    """
    expanded = set(api_key_sensitivities)
    to_process = list(api_key_sensitivities)

    while to_process:
        current = to_process.pop()
        if current in config.sensitivities:
            for included in config.sensitivities[current].includes:
                if included not in expanded:
                    expanded.add(included)
                    to_process.append(included)

    return expanded
