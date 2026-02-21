# Indexing

## Overview

Indexing discovers note files on disk, extracts sensitivity metadata, and persists it to the SQLite index. It is designed to be incremental: only files whose modification time has changed since the last index run are re-processed.

## Requirements

### File Discovery

- The system MUST discover files by expanding each file group's glob pattern.
- The system MUST support recursive glob patterns using `**`.
- The system MUST resolve `~` and environment variables in path patterns.
- The system MUST silently skip glob patterns that match no files.
- The system MUST collect files from all configured file groups in a single indexing pass.

### Incremental Processing

- The system MUST skip re-indexing a file if its modification time (`mtime`) is unchanged from the value recorded in the index.
- The system MUST re-index a file if its modification time has changed.
- The system MUST re-index a file if it has no existing record in the index.
- The system SHOULD report counts of indexed, skipped, and errored files after each run.

### Note Identity

- Each note MUST be assigned a UUID derived deterministically from its content hash (SHA-256).
- If a file's content has not changed but its path has (rename), the system SHOULD reuse the existing UUID if the content hash matches an existing record.
- The system MUST use the UUID as the stable public identifier for a note, not the file path.

### Metadata Extraction

- The system MUST compute a SHA-256 hash of each file's content and store it in the index.
- The system MUST detect sensitivity levels for each file by running the sensitivity detection algorithm against its full content.
- The system MUST store the detected sensitivities (set), effective sensitivity (single value), file group name, and file path alongside the UUID and content hash.
- The system MUST record the file's modification time at the time of indexing.

### Deletion Handling

- The system MUST remove index entries for files that no longer exist on disk.
- The system MUST determine which indexed paths are absent from the current glob expansion and delete those entries.

### Error Handling

- The system MUST catch errors on a per-file basis and continue indexing remaining files.
- The system MUST increment an error counter for each failed file.
- The system SHOULD log the error and file path for each failure.
- The system MUST NOT abort the entire indexing run due to a single file error.

### Progress Reporting

- The system MAY accept a progress callback to report indexing progress to the caller.
- The CLI MUST display a progress bar during indexing using Rich.

## Data Model

```
NoteMetadata:
  uuid: str                          # Deterministic UUID from content hash
  file_path: str                     # Absolute path to the file
  file_group: str                    # Name of the file group that matched
  detected_sensitivities: set[str]   # All matched sensitivity levels
  effective_sensitivity: str         # Single resolved sensitivity
  content_hash: str                  # SHA-256 of file content
  indexed_at: datetime               # When this record was last updated
  file_mtime: float                  # File modification time at index time
```

## Behavior

### Full Index Run (`index_all`)

1. Load all existing note metadata from the SQLite index into a path-keyed map.
2. Expand all file group glob patterns to collect the current set of file paths.
3. For each discovered file:
   a. Check if an existing record exists and if `mtime` is unchanged; if so, skip.
   b. Read file content.
   c. Compute SHA-256 content hash.
   d. Run sensitivity detection to get detected sensitivities and effective sensitivity.
   e. Assign or reuse UUID.
   f. Create/update `NoteMetadata`.
4. Batch-upsert all new/updated records to the SQLite index.
5. Delete index entries for paths no longer present in the glob expansion.
6. Return statistics: `{indexed: int, skipped: int, errors: int}`.

### UUID Assignment

1. Compute SHA-256 of the file content.
2. Use the first 32 hex characters as a UUID (formatted as UUID4 without version bits).
3. If an existing record with the same content hash exists under a different path, reuse that UUID.

## Statistics

| Field | Description |
|-------|-------------|
| `indexed` | Files newly processed or updated |
| `skipped` | Files unchanged since last index |
| `errors` | Files that failed to process |
