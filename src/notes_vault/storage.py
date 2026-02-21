"""SQLite database layer for notes-vault."""

import json
import sqlite3
from datetime import datetime
from uuid import UUID

from notes_vault.config import get_db_path
from notes_vault.models import AccessLogEntry, NoteMetadata


def init_db() -> None:
    """Initialize the database schema."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                uuid TEXT PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                file_group TEXT NOT NULL,
                detected_sensitivities TEXT,
                last_modified TIMESTAMP,
                last_indexed TIMESTAMP,
                content_hash TEXT,
                content TEXT
            )
        """)

        # Migrate existing databases that lack the content column
        try:
            conn.execute("ALTER TABLE notes ADD COLUMN content TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Standalone FTS5 table for full-text search.
        # Rowid matches notes.rowid so the tables can be joined efficiently.
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(content)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                api_key TEXT,
                action TEXT,
                note_uuid TEXT,
                granted BOOLEAN
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _upsert_fts(conn: sqlite3.Connection, note_uuid: str, content: str | None) -> None:
    """Delete and re-insert the FTS5 entry for a note, identified by notes.rowid."""
    row = conn.execute("SELECT rowid FROM notes WHERE uuid = ?", (note_uuid,)).fetchone()
    if row is None:
        return
    rowid = row[0]
    conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (rowid,))
    if content is not None:
        conn.execute(
            "INSERT INTO notes_fts(rowid, content) VALUES (?, ?)", (rowid, content)
        )


def upsert_note(note: NoteMetadata, content: str | None = None) -> None:
    """Insert or update a note in the database."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO notes (uuid, file_path, file_group, detected_sensitivities,
                               last_modified, last_indexed, content_hash, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                file_path = excluded.file_path,
                file_group = excluded.file_group,
                detected_sensitivities = excluded.detected_sensitivities,
                last_modified = excluded.last_modified,
                last_indexed = excluded.last_indexed,
                content_hash = excluded.content_hash,
                content = excluded.content
            """,
            (
                str(note.uuid),
                note.file_path,
                note.file_group,
                json.dumps(sorted(list(note.detected_sensitivities))),
                note.last_modified.isoformat(),
                note.last_indexed.isoformat(),
                note.content_hash,
                content,
            ),
        )
        _upsert_fts(conn, str(note.uuid), content)
        conn.commit()
    finally:
        conn.close()


def get_note_by_uuid(uuid: UUID) -> NoteMetadata | None:
    """Get a note by its UUID."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM notes WHERE uuid = ?", (str(uuid),)).fetchone()
        if not row:
            return None

        return NoteMetadata(
            uuid=UUID(row["uuid"]),
            file_path=row["file_path"],
            file_group=row["file_group"],
            detected_sensitivities=set(json.loads(row["detected_sensitivities"])),
            last_modified=datetime.fromisoformat(row["last_modified"]),
            last_indexed=datetime.fromisoformat(row["last_indexed"]),
            content_hash=row["content_hash"],
        )
    finally:
        conn.close()


def get_note_by_path(file_path: str) -> NoteMetadata | None:
    """Get a note by its file path."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM notes WHERE file_path = ?", (file_path,)).fetchone()
        if not row:
            return None

        return NoteMetadata(
            uuid=UUID(row["uuid"]),
            file_path=row["file_path"],
            file_group=row["file_group"],
            detected_sensitivities=set(json.loads(row["detected_sensitivities"])),
            last_modified=datetime.fromisoformat(row["last_modified"]),
            last_indexed=datetime.fromisoformat(row["last_indexed"]),
            content_hash=row["content_hash"],
        )
    finally:
        conn.close()


def list_notes(sensitivities: set[str] | None = None) -> list[NoteMetadata]:
    """List notes, optionally filtered by sensitivity levels.

    A note is accessible if ANY of its detected sensitivities matches
    one of the requested sensitivity levels.
    """
    conn = get_db_connection()
    try:
        if sensitivities:
            # Filter by detected_sensitivities: match if any detected sensitivity is in the set
            # detected_sensitivities is stored as JSON array like '["llm","private"]'
            placeholders = ",".join("?" * len(sensitivities))
            # Use json_each to check if any element of the JSON array matches
            query = f"""
                SELECT DISTINCT n.* FROM notes n
                WHERE EXISTS (
                    SELECT 1 FROM json_each(n.detected_sensitivities) AS j
                    WHERE j.value IN ({placeholders})
                )
            """
            rows = conn.execute(query, tuple(sensitivities)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM notes").fetchall()

        return [
            NoteMetadata(
                uuid=UUID(row["uuid"]),
                file_path=row["file_path"],
                file_group=row["file_group"],
                detected_sensitivities=set(json.loads(row["detected_sensitivities"])),
                last_modified=datetime.fromisoformat(row["last_modified"]),
                last_indexed=datetime.fromisoformat(row["last_indexed"]),
                content_hash=row["content_hash"],
            )
            for row in rows
        ]
    finally:
        conn.close()


def upsert_notes_batch(notes_with_content: list[tuple[NoteMetadata, str]]) -> None:
    """Insert or update multiple notes in a single transaction."""
    if not notes_with_content:
        return
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT INTO notes (uuid, file_path, file_group, detected_sensitivities,
                               last_modified, last_indexed, content_hash, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                file_path = excluded.file_path,
                file_group = excluded.file_group,
                detected_sensitivities = excluded.detected_sensitivities,
                last_modified = excluded.last_modified,
                last_indexed = excluded.last_indexed,
                content_hash = excluded.content_hash,
                content = excluded.content
            """,
            [
                (
                    str(note.uuid),
                    note.file_path,
                    note.file_group,
                    json.dumps(sorted(list(note.detected_sensitivities))),
                    note.last_modified.isoformat(),
                    note.last_indexed.isoformat(),
                    note.content_hash,
                    content,
                )
                for note, content in notes_with_content
            ],
        )
        # Sync FTS5 index for each upserted note
        for note, content in notes_with_content:
            _upsert_fts(conn, str(note.uuid), content)
        conn.commit()
    finally:
        conn.close()


def search_notes_fts(
    query: str,
    sensitivities: set[str] | None = None,
    case_sensitive: bool = False,
) -> list[tuple[NoteMetadata, list[tuple[int, str]]]]:
    """Search notes using FTS5 (case-insensitive) or INSTR (case-sensitive).

    Returns a list of (note, matching_lines) tuples where matching_lines is a
    list of (line_number, line_text) pairs.

    A note is searchable if ANY of its detected sensitivities matches
    one of the requested sensitivity levels.
    """
    conn = get_db_connection()
    try:
        if case_sensitive:
            # INSTR is case-sensitive in SQLite
            if sensitivities:
                placeholders = ",".join("?" * len(sensitivities))
                sql = f"""
                    SELECT n.* FROM notes n
                    WHERE INSTR(n.content, ?) > 0
                    AND EXISTS (
                        SELECT 1 FROM json_each(n.detected_sensitivities) AS j
                        WHERE j.value IN ({placeholders})
                    )
                """
                rows = conn.execute(sql, (query, *tuple(sensitivities))).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE INSTR(content, ?) > 0", (query,)
                ).fetchall()
        else:
            # Wrap in double quotes for exact phrase matching in FTS5
            fts_query = '"' + query.replace('"', '""') + '"'
            if sensitivities:
                placeholders = ",".join("?" * len(sensitivities))
                sql = f"""
                    SELECT DISTINCT n.* FROM notes_fts
                    JOIN notes n ON notes_fts.rowid = n.rowid
                    WHERE notes_fts MATCH ?
                    AND EXISTS (
                        SELECT 1 FROM json_each(n.detected_sensitivities) AS j
                        WHERE j.value IN ({placeholders})
                    )
                    ORDER BY n.rowid
                """
                rows = conn.execute(sql, (fts_query, *tuple(sensitivities))).fetchall()
            else:
                rows = conn.execute(
                    "SELECT n.* FROM notes_fts"
                    " JOIN notes n ON notes_fts.rowid = n.rowid"
                    " WHERE notes_fts MATCH ?"
                    " ORDER BY rank",
                    (fts_query,),
                ).fetchall()

        results = []
        for row in rows:
            note = NoteMetadata(
                uuid=UUID(row["uuid"]),
                file_path=row["file_path"],
                file_group=row["file_group"],
                detected_sensitivities=set(json.loads(row["detected_sensitivities"])),
                last_modified=datetime.fromisoformat(row["last_modified"]),
                last_indexed=datetime.fromisoformat(row["last_indexed"]),
                content_hash=row["content_hash"],
            )
            note_content = row["content"] or ""
            matching_lines = [
                (line_num, line.strip())
                for line_num, line in enumerate(note_content.splitlines(), start=1)
                if (query in line if case_sensitive else query.lower() in line.lower())
            ]
            results.append((note, matching_lines))

        return results
    finally:
        conn.close()


def delete_note_by_path(file_path: str) -> None:
    """Delete a note from the database by its file path."""
    conn = get_db_connection()
    try:
        # Remove FTS5 entry before deleting from notes
        row = conn.execute(
            "SELECT rowid FROM notes WHERE file_path = ?", (file_path,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM notes_fts WHERE rowid = ?", (row[0],))
        conn.execute("DELETE FROM notes WHERE file_path = ?", (file_path,))
        conn.commit()
    finally:
        conn.close()


def log_access(entry: AccessLogEntry) -> None:
    """Log an access attempt."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO access_log (timestamp, api_key, action, note_uuid, granted)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.timestamp.isoformat(),
                entry.api_key,
                entry.action,
                str(entry.note_uuid) if entry.note_uuid else None,
                entry.granted,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def clear_all_notes() -> None:
    """Clear all notes from the database."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM notes_fts")
        conn.execute("DELETE FROM notes")
        conn.commit()
    finally:
        conn.close()
