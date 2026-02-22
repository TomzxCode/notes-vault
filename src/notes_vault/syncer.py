"""File discovery and export."""

import re
import shutil
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch
from pathlib import Path

import structlog

from notes_vault.config import load_config
from notes_vault.models import Config, Consumer

logger = structlog.get_logger()

_pattern_cache: dict[str, re.Pattern[str]] = {}


def _file_uuid(file_path: Path) -> str:
    """Generate a deterministic UUID5 based on the absolute file path."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, str(file_path.resolve())))


def _matches_any(content: str, patterns: list[str]) -> bool:
    """Return True if content matches any of the given regex patterns."""
    for pattern in patterns:
        if pattern not in _pattern_cache:
            _pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)
        if _pattern_cache[pattern].search(content):
            return True
    return False


def _matches_path_glob(file_path: Path, patterns: list[str]) -> bool:
    """Return True if file_path matches any of the given glob patterns."""
    path_str = str(file_path)
    for pattern in patterns:
        if fnmatch(path_str, pattern) or fnmatch(file_path.name, pattern):
            return True
    return False


def _scan(
    base_path: Path,
    glob_pattern: str,
    on_file_found: Callable[[], None] | None,
) -> list[Path]:
    """Scan base_path with glob_pattern and return matching file paths."""
    result = []
    for file_path in base_path.glob(glob_pattern):
        if file_path.is_file():
            result.append(file_path)
            if on_file_found:
                on_file_found()
    return result


def _collect_files(
    config: Config,
    on_file_found: Callable[[], None] | None = None,
    workers: int | None = None,
) -> list[Path]:
    """Collect all files from configured file groups.

    Recursive globs are split by top-level subdirectory to maximise parallelism.
    """
    tasks: list[tuple[Path, str]] = []  # (base_path, glob_pattern)

    for fg in config.files.values():
        pattern = Path(fg.path).expanduser()
        pattern_str = str(pattern)
        if "**" in pattern_str:
            base_path = Path(pattern_str.split("**")[0])
            recursive_suffix = pattern_str.replace(str(base_path), "").lstrip("/")
            file_pattern = recursive_suffix.split("/")[-1]
            if "**" in file_pattern:
                file_pattern = "*"
            if base_path.exists():
                subdirs = [d for d in base_path.iterdir() if d.is_dir()]
                if subdirs:
                    tasks.append((base_path, file_pattern))
                    for subdir in subdirs:
                        tasks.append((subdir, recursive_suffix))
                    continue
            tasks.append((base_path, recursive_suffix))
        else:
            tasks.append((Path(), pattern_str))

    if not tasks:
        return []

    result: list[Path] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_scan, bp, gp, on_file_found) for bp, gp in tasks]
        for future in as_completed(futures):
            result.extend(future.result())
    return result


def _unique_dest(target: Path, file_path: Path) -> Path:
    """Compute a non-colliding destination path in target for file_path."""
    dest = target / file_path.name
    if not dest.exists():
        return dest
    stem = file_path.stem
    suffix = file_path.suffix
    i = 1
    while dest.exists():
        dest = target / f"{stem}_{i}{suffix}"
        i += 1
    return dest


def sync_consumer(
    consumer_name: str,
    consumer: Consumer,
    config: Config,
    on_file_found: Callable[[], None] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    workers: int | None = None,
) -> dict[str, int]:
    """Export files matching a consumer's queries to their target directory."""
    target = Path(consumer.target).expanduser()

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {"exported": 0, "skipped": 0, "errors": 0}

    all_files = _collect_files(config, on_file_found=on_file_found, workers=workers)
    total = len(all_files)

    dest_lock = threading.Lock()

    def _process(file_path: Path) -> str:
        if _matches_path_glob(file_path, consumer.exclude_paths):
            return "skipped"

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to read file", file_path=str(file_path), error=str(e))
            return "errors"

        if _matches_any(content, consumer.exclude_queries):
            return "skipped"

        if not consumer.include_queries or not _matches_any(content, consumer.include_queries):
            return "skipped"

        if consumer.rename:
            dest = target / (_file_uuid(file_path) + file_path.suffix)
            shutil.copy2(file_path, dest)
        else:
            with dest_lock:
                dest = _unique_dest(target, file_path)
                shutil.copy2(file_path, dest)

        logger.info("Exported", src=str(file_path), dest=str(dest), consumer=consumer_name)
        return "exported"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_process, fp): None for fp in all_files}
        for n_done, future in enumerate(as_completed(futures), start=1):
            stats[future.result()] += 1
            if progress_callback:
                progress_callback(n_done, total)

    return stats


def sync_all(consumer_name: str | None = None) -> dict[str, dict[str, int]]:
    """Sync all consumers, or just one if consumer_name is specified."""
    config = load_config()
    consumers = config.consumers

    if consumer_name:
        if consumer_name not in consumers:
            raise ValueError(f"Consumer '{consumer_name}' not found")
        consumers = {consumer_name: consumers[consumer_name]}

    results = {}
    for name, consumer in consumers.items():
        logger.info("Syncing consumer", consumer=name, target=consumer.target)
        results[name] = sync_consumer(name, consumer, config)

    return results
