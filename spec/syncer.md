# Syncer

## Overview

The syncer is the core engine of Notes Vault. It discovers files, applies consumer query matching, and exports matching files to consumer target directories. There is no persistent index or database - each sync run operates directly on the filesystem.

## Requirements

### File Discovery

- The system MUST discover files by expanding each file group's glob pattern.
- The system MUST support recursive glob patterns using `**`.
- The system MUST resolve `~` in path patterns.
- The system MUST silently skip glob patterns that match no files.
- The system MUST collect files from all configured file groups, scanning multiple groups in parallel.

### Query Matching

- For each file, the system MUST check the consumer's `exclude_queries` first.
- If any `exclude_queries` pattern matches the file content, the system MUST skip the file.
- If at least one `include_queries` pattern matches the file content, the system MUST export the file.
- If no `include_queries` pattern matches, the system MUST skip the file.
- A consumer with an empty `include_queries` list exports nothing.
- The system MUST cache compiled regex patterns to avoid recompilation across files.
- Pattern matching MUST be case-insensitive.

### Export

- The system MUST delete the consumer's target directory before exporting, then recreate it empty.
- The system MUST copy matching files into the target directory.
- When `rename: false`, the system MUST preserve the original filename.
- When `rename: false` and filenames collide, the system MUST append a numeric suffix (e.g., `note_1.md`).
- When `rename: true`, the system MUST rename files to `<uuid5><extension>` where the UUID is derived from the absolute source file path using `uuid.uuid5(uuid.NAMESPACE_URL, str(file_path.resolve()))`.
- The system MUST use `shutil.copy2` to preserve file metadata.
- The system MUST process files in parallel using a thread pool.
- A lock MUST guard destination path computation and copy for `rename: false` to prevent TOCTOU races.

### Error Handling

- The system MUST catch read errors on a per-file basis and continue processing remaining files.
- The system MUST count errored files separately from skipped and exported files.
- The system SHOULD log warnings for files that fail to read.
- The system MUST NOT abort a sync run due to a single file error.

### Progress Reporting

- The system MUST accept optional callbacks for file-found events and export progress.
- The CLI MUST display a progress bar during sync using Rich.

### Statistics

- `sync_consumer` MUST return a dict with keys `exported`, `skipped`, and `errors`.
- The CLI MUST print these statistics after each consumer sync.

## Data Model

```
sync_consumer(consumer_name, consumer, config, on_file_found?, progress_callback?, workers?) -> dict[str, int]
sync_all(consumer_name?) -> dict[str, dict[str, int]]
```

## Behavior

### `sync_consumer`

1. Resolve the target directory path (expand `~`).
2. Delete the target directory if it exists; create it fresh.
3. Collect all files from all file groups in parallel.
4. For each file (in parallel):
   a. Read file content (UTF-8). On error, increment `errors` and skip.
   b. If any `exclude_queries` pattern matches, increment `skipped` and skip.
   c. If no `include_queries` pattern matches, increment `skipped` and skip.
   d. Compute destination path (UUID-renamed or original filename, with collision avoidance).
   e. Copy file to destination. Increment `exported`.
5. Return `{exported, skipped, errors}`.

### `sync_all`

1. Load config.
2. If `consumer_name` is given, validate it exists and restrict to that consumer only.
3. For each consumer, call `sync_consumer` and collect results.
4. Return a dict keyed by consumer name.

## Statistics

| Field | Description |
|-------|-------------|
| `exported` | Files copied to the target directory |
| `skipped` | Files excluded by query rules |
| `errors` | Files that could not be read |
