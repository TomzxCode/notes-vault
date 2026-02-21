"""User-facing commands for listing and accessing notes."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated
from uuid import UUID

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.access_control import get_accessible_notes, get_note_if_accessible, resolve_key
from notes_vault.models import ApiKey
from notes_vault.storage import init_db

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
    table.add_column("Sensitivity", style="green")
    table.add_column("Group", style="yellow")

    for note in notes:
        table.add_row(
            str(note.uuid),
            note.effective_sensitivity,
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

    notes = get_accessible_notes(api_key.key_name)

    if not notes:
        console.print("[yellow]No accessible notes found[/yellow]")
        return

    # Build list of accessible file paths
    file_paths = [note.file_path for note in notes]

    if not file_paths:
        console.print("[yellow]No accessible notes found[/yellow]")
        return

    # Use ripgrep to search through files
    rg_args = [
        "rg",
        "--json",
        "--line-number",
        "--no-heading",
    ]

    if not case_sensitive:
        rg_args.append("--ignore-case")

    rg_args.append(query_string)

    try:
        batch_size = 100
        batches = [file_paths[i:i + batch_size] for i in range(0, len(file_paths), batch_size)]
        combined_stdout = []

        for batch in batches:
            result = subprocess.run(
                rg_args + batch,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit (no matches)
            )

            if result.returncode not in [0, 1]:
                # Exit code 2+ means error
                console.print(f"[red]Error running ripgrep:[/red] {result.stderr}")
                return

            if result.stdout:
                combined_stdout.append(result.stdout)

        if not combined_stdout:
            console.print(f"[yellow]No matches found for query: '{query_string}'[/yellow]")
            return

        # Parse ripgrep JSON output
        matches_by_file = {}
        for line in "".join(combined_stdout).strip().split("\n"):
            if not line:
                continue

            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    file_path = data["data"]["path"]["text"]
                    line_num = data["data"]["line_number"]
                    line_text = data["data"]["lines"]["text"].strip()

                    if file_path not in matches_by_file:
                        matches_by_file[file_path] = []

                    matches_by_file[file_path].append((line_num, line_text))

            except json.JSONDecodeError, KeyError:
                continue

        if not matches_by_file:
            console.print(f"[yellow]No matches found for query: '{query_string}'[/yellow]")
            return

        # Map file paths back to notes
        notes_by_path = {note.file_path: note for note in notes}
        matched_notes = []

        for file_path, matching_lines in matches_by_file.items():
            if file_path in notes_by_path:
                matched_notes.append((notes_by_path[file_path], matching_lines))

        if with_context:
            # Detailed mode: show match context
            console.print(
                f"\n[green]Found {len(matched_notes)} notes matching '{query_string}'[/green]\n"
            )

            for note, matching_lines in matched_notes:
                console.print(f"[cyan]UUID:[/cyan] {note.uuid}")
                console.print(f"[cyan]Sensitivity:[/cyan] {note.effective_sensitivity}")
                console.print(f"[cyan]Group:[/cyan] {note.file_group}")
                console.print(f"[cyan]Matches:[/cyan] {len(matching_lines)} line(s)")

                # Show all matching lines
                for line_num, line_content in matching_lines:
                    console.print(f"  [dim]Line {line_num}:[/dim] {line_content}")

                console.print()

            console.print(f"[cyan]Total:[/cyan] {len(matched_notes)} notes with matches")
        else:
            # Default: just print UUIDs
            for note, _ in matched_notes:
                console.print(str(note.uuid))

    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] ripgrep (rg) not found. "
            "Please install ripgrep to use the query command."
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
