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
                effective_sensitivity TEXT NOT NULL,
                last_modified TIMESTAMP,
                last_indexed TIMESTAMP,
                content_hash TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_effective_sensitivity ON notes(effective_sensitivity)"
        )

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


def upsert_note(note: NoteMetadata) -> None:
    """Insert or update a note in the database."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO notes (uuid, file_path, file_group, detected_sensitivities,
                               effective_sensitivity, last_modified, last_indexed, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                file_path = excluded.file_path,
                file_group = excluded.file_group,
                detected_sensitivities = excluded.detected_sensitivities,
                effective_sensitivity = excluded.effective_sensitivity,
                last_modified = excluded.last_modified,
                last_indexed = excluded.last_indexed,
                content_hash = excluded.content_hash
            """,
            (
                str(note.uuid),
                note.file_path,
                note.file_group,
                json.dumps(sorted(list(note.detected_sensitivities))),
                note.effective_sensitivity,
                note.last_modified.isoformat(),
                note.last_indexed.isoformat(),
                note.content_hash,
            ),
        )
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
            effective_sensitivity=row["effective_sensitivity"],
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
            effective_sensitivity=row["effective_sensitivity"],
            last_modified=datetime.fromisoformat(row["last_modified"]),
            last_indexed=datetime.fromisoformat(row["last_indexed"]),
            content_hash=row["content_hash"],
        )
    finally:
        conn.close()


def list_notes(sensitivities: set[str] | None = None) -> list[NoteMetadata]:
    """List notes, optionally filtered by sensitivity levels."""
    conn = get_db_connection()
    try:
        if sensitivities:
            placeholders = ",".join("?" * len(sensitivities))
            query = f"SELECT * FROM notes WHERE effective_sensitivity IN ({placeholders})"
            rows = conn.execute(query, tuple(sensitivities)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM notes").fetchall()

        return [
            NoteMetadata(
                uuid=UUID(row["uuid"]),
                file_path=row["file_path"],
                file_group=row["file_group"],
                detected_sensitivities=set(json.loads(row["detected_sensitivities"])),
                effective_sensitivity=row["effective_sensitivity"],
                last_modified=datetime.fromisoformat(row["last_modified"]),
                last_indexed=datetime.fromisoformat(row["last_indexed"]),
                content_hash=row["content_hash"],
            )
            for row in rows
        ]
    finally:
        conn.close()


def upsert_notes_batch(notes: list[NoteMetadata]) -> None:
    """Insert or update multiple notes in a single transaction."""
    if not notes:
        return
    conn = get_db_connection()
    try:
        conn.executemany(
            """
            INSERT INTO notes (uuid, file_path, file_group, detected_sensitivities,
                               effective_sensitivity, last_modified, last_indexed, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                file_path = excluded.file_path,
                file_group = excluded.file_group,
                detected_sensitivities = excluded.detected_sensitivities,
                effective_sensitivity = excluded.effective_sensitivity,
                last_modified = excluded.last_modified,
                last_indexed = excluded.last_indexed,
                content_hash = excluded.content_hash
            """,
            [
                (
                    str(note.uuid),
                    note.file_path,
                    note.file_group,
                    json.dumps(sorted(list(note.detected_sensitivities))),
                    note.effective_sensitivity,
                    note.last_modified.isoformat(),
                    note.last_indexed.isoformat(),
                    note.content_hash,
                )
                for note in notes
            ],
        )
        conn.commit()
    finally:
        conn.close()


def delete_note_by_path(file_path: str) -> None:
    """Delete a note from the database by its file path."""
    conn = get_db_connection()
    try:
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
        conn.execute("DELETE FROM notes")
        conn.commit()
    finally:
        conn.close()
