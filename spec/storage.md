# Storage

## Overview

Notes Vault uses a SQLite database as the metadata index for indexed notes and as the store for access log entries. The database is an implementation detail and is not intended to be accessed directly by users or external tools.

## Requirements

### Initialization

- The system MUST create the SQLite database file and required tables on first use if they do not exist.
- The system MUST use `IF NOT EXISTS` semantics for table creation to allow safe re-initialization.
- The system MUST migrate existing databases lacking the `content` column by running `ALTER TABLE notes ADD COLUMN content TEXT`.

### Notes Table

- The system MUST store one row per note, keyed by UUID.
- The system MUST store the following fields per note: `uuid`, `file_path`, `file_group`, `detected_sensitivities`, `effective_sensitivity`, `content_hash`, `last_indexed`, `last_modified`, `content`.
- The system MUST serialize `detected_sensitivities` (a set) as a JSON array for storage.
- The system MUST deserialize `detected_sensitivities` back into a set on read.
- The system MUST store the full text content of each note to support full-text search.
- The system MUST use upsert semantics (`INSERT ... ON CONFLICT DO UPDATE`) when writing note records.
- The system MUST support batch upsert of multiple notes in a single transaction for efficiency.

### Full-Text Search

- The system MUST maintain a standalone FTS5 virtual table (`notes_fts`) for full-text search over note content.
- The system MUST keep `notes_fts` in sync with the `notes` table by updating it on every upsert and delete.
- The system MUST use FTS5 phrase matching for case-insensitive search.
- The system MUST use SQLite `INSTR` for case-sensitive search.
- The system MUST filter search results to a specified set of effective sensitivity values.

### Querying Notes

- The system MUST support retrieving a single note by UUID.
- The system MUST support retrieving a single note by file path.
- The system MUST support listing all notes with optional filtering by a set of effective sensitivity values.
- The system SHOULD use parameterized queries to prevent SQL injection.

### Deletion

- The system MUST support deleting a single note by file path, including its FTS5 entry.
- The system MUST support clearing all notes from the database, including the FTS5 table.

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
    file_path TEXT NOT NULL UNIQUE,
    file_group TEXT NOT NULL,
    detected_sensitivities TEXT,       -- JSON array
    effective_sensitivity TEXT NOT NULL,
    last_modified TIMESTAMP,
    last_indexed TIMESTAMP,
    content_hash TEXT,
    content TEXT
);

CREATE INDEX IF NOT EXISTS idx_effective_sensitivity ON notes(effective_sensitivity);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(content);

CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    api_key TEXT,
    action TEXT,
    note_uuid TEXT,                    -- nullable
    granted BOOLEAN
);
```

## Operations

| Operation | Description |
|-----------|-------------|
| `init_db()` | Create tables if not present; migrate existing schema |
| `upsert_note(note, content)` | Insert or update a single note record and its FTS5 entry |
| `upsert_notes_batch(notes)` | Insert or update multiple notes in one transaction |
| `get_note_by_uuid(uuid)` | Return `NoteMetadata` or `None` |
| `get_note_by_path(path)` | Return `NoteMetadata` or `None` |
| `list_notes(sensitivities?)` | Return list of `NoteMetadata`, optionally filtered by sensitivity |
| `search_notes_fts(query, sensitivities?, case_sensitive?)` | Full-text search returning `(NoteMetadata, [(line_num, line_text)])` tuples |
| `delete_note_by_path(path)` | Remove note record and FTS5 entry by file path |
| `clear_all_notes()` | Remove all note records and FTS5 entries |
| `log_access(entry)` | Append an access log entry |

## Notes on Serialization

`detected_sensitivities` is stored as a JSON array (e.g., `'["private", "work"]'`). On read, the string is parsed back to a `set[str]`.
