# Storage

## Overview

Notes Vault uses a SQLite database as the metadata index for indexed notes and as the store for access log entries. The database is an implementation detail and is not intended to be accessed directly by users or external tools.

## Requirements

### Initialization

- The system MUST create the SQLite database file and required tables on first use if they do not exist.
- The system MUST use `IF NOT EXISTS` semantics for table creation to allow safe re-initialization.

### Notes Table

- The system MUST store one row per note, keyed by UUID.
- The system MUST store the following fields per note: `uuid`, `file_path`, `file_group`, `detected_sensitivities`, `effective_sensitivity`, `content_hash`, `indexed_at`, `file_mtime`.
- The system MUST serialize `detected_sensitivities` (a set) as a comma-separated string for storage.
- The system MUST deserialize `detected_sensitivities` back into a set on read.
- The system MUST use `INSERT OR REPLACE` (upsert) semantics when writing note records.
- The system MUST support batch upsert of multiple notes in a single transaction for efficiency.

### Querying Notes

- The system MUST support retrieving a single note by UUID.
- The system MUST support retrieving a single note by file path.
- The system MUST support listing all notes with optional filtering by a set of effective sensitivity values.
- The system SHOULD use parameterized queries to prevent SQL injection.

### Deletion

- The system MUST support deleting a single note by file path.
- The system MUST support clearing all notes from the database (used for full re-index).

### Access Log Table

- The system MUST store access log entries in a separate `access_log` table.
- The system MUST store the following fields per entry: `timestamp`, `api_key`, `action`, `note_uuid` (nullable), `granted`.
- The system MUST insert access log entries in append-only fashion (no updates or deletes).

### Connections

- The system MUST use `sqlite3.Row` as the row factory to allow column-name-based access.
- The system MAY open a new connection per operation or reuse a connection within a single request.

## Schema

```sql
CREATE TABLE IF NOT EXISTS notes (
    uuid TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_group TEXT NOT NULL,
    detected_sensitivities TEXT NOT NULL,  -- comma-separated
    effective_sensitivity TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at TEXT NOT NULL,              -- ISO 8601 datetime
    file_mtime REAL NOT NULL               -- Unix timestamp
);

CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,               -- ISO 8601 datetime
    api_key TEXT NOT NULL,
    action TEXT NOT NULL,
    note_uuid TEXT,                        -- nullable
    granted INTEGER NOT NULL               -- 0 or 1
);
```

## Operations

| Operation | Description |
|-----------|-------------|
| `init_db()` | Create tables if not present |
| `upsert_note(note)` | Insert or replace a single note record |
| `upsert_notes_batch(notes)` | Insert or replace multiple notes in one transaction |
| `get_note_by_uuid(uuid)` | Return `NoteMetadata` or `None` |
| `get_note_by_path(path)` | Return `NoteMetadata` or `None` |
| `list_notes(sensitivities?)` | Return list of `NoteMetadata`, optionally filtered |
| `delete_note_by_path(path)` | Remove note record by file path |
| `clear_all_notes()` | Remove all note records |
| `log_access(entry)` | Append an access log entry |

## Notes on Serialization

`detected_sensitivities` is stored as a comma-separated string (e.g., `"private,work"`) because SQLite has no native set type. An empty set is stored as an empty string `""`. On read, the string is split on `,` and converted to a `set[str]`, with the empty string case returning an empty set.
