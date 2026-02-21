"""User-facing commands for listing and accessing notes."""

import os
import sys
from pathlib import Path
from typing import Annotated
from uuid import UUID

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.access_control import get_accessible_notes, get_note_if_accessible, resolve_key
from notes_vault.config import load_config
from notes_vault.models import ApiKey
from notes_vault.sensitivity import expand_access
from notes_vault.storage import init_db, search_notes_fts

console = Console()
stderr = Console(stderr=True)


def _resolve_key(key: str | None) -> ApiKey | None:
    return resolve_key(key or os.environ.get("NOTES_VAULT_KEY"))


def list_notes(
    key: Annotated[str | None, cyclopts.Parameter(help="API key")] = None,
):
    """List all notes accessible by the given API key."""
    init_db()

    api_key = _resolve_key(key)
    if not api_key:
        console.print("[red]Error:[/red] Invalid API key")
        return

    notes = get_accessible_notes(api_key.key_name)

    if not notes:
        console.print("[yellow]No accessible notes found[/yellow]")
        return

    table = Table(title=f"Notes accessible by '{api_key.key_name}'")
    table.add_column("UUID", style="cyan")
    table.add_column("Sensitivities", style="green")
    table.add_column("Group", style="yellow")

    for note in notes:
        sensitivities_str = ", ".join(sorted(note.detected_sensitivities))
        table.add_row(
            str(note.uuid),
            sensitivities_str,
            note.file_group,
        )

    console.print(table)
    console.print(f"\n[cyan]Total:[/cyan] {len(notes)} notes")


def get(
    uuid: Annotated[str, cyclopts.Parameter(help="Note UUID")],
    key: Annotated[str | None, cyclopts.Parameter(help="API key")] = None,
):
    """Get the content of a note by UUID if accessible."""
    init_db()

    api_key = _resolve_key(key)
    if not api_key:
        stderr.print("[red]Error:[/red] Invalid API key")
        sys.exit(1)

    try:
        note_uuid = UUID(uuid)
    except ValueError:
        stderr.print(f"[red]Error:[/red] Invalid UUID: {uuid}")
        sys.exit(1)

    note = get_note_if_accessible(api_key.key_name, note_uuid)

    if not note:
        stderr.print("[red]Access denied or note not found[/red]")
        sys.exit(1)

    try:
        content = Path(note.file_path).read_text(encoding="utf-8")
        print(content, end="")
    except Exception as e:
        stderr.print(f"[red]Error reading file:[/red] {e}")
        sys.exit(1)


def query(
    query_string: Annotated[str, cyclopts.Parameter(help="Search query")],
    key: Annotated[str | None, cyclopts.Parameter(help="API key")] = None,
    case_sensitive: Annotated[bool, cyclopts.Parameter(help="Case sensitive search")] = False,
    with_context: Annotated[
        bool, cyclopts.Parameter(help="Show match details and line content")
    ] = False,
):
    """Search for notes matching a query within accessible notes."""
    init_db()

    api_key = _resolve_key(key)
    if not api_key:
        console.print("[red]Error:[/red] Invalid API key")
        return

    config = load_config()
    accessible_sensitivities = expand_access(api_key.sensitivities, config)

    matched_notes = search_notes_fts(query_string, accessible_sensitivities, case_sensitive)

    if not matched_notes:
        console.print(f"[yellow]No matches found for query: '{query_string}'[/yellow]")
        return

    if with_context:
        console.print(
            f"\n[green]Found {len(matched_notes)} notes matching '{query_string}'[/green]\n"
        )

        for note, matching_lines in matched_notes:
            sensitivities_str = ", ".join(sorted(note.detected_sensitivities))
            console.print(f"[cyan]UUID:[/cyan] {note.uuid}")
            console.print(f"[cyan]Sensitivities:[/cyan] {sensitivities_str}")
            console.print(f"[cyan]Group:[/cyan] {note.file_group}")
            console.print(f"[cyan]Matches:[/cyan] {len(matching_lines)} line(s)")

            for line_num, line_content in matching_lines:
                console.print(f"  [dim]Line {line_num}:[/dim] {line_content}")

            console.print()

        console.print(f"[cyan]Total:[/cyan] {len(matched_notes)} notes with matches")
    else:
        for note, _ in matched_notes:
            console.print(str(note.uuid))
