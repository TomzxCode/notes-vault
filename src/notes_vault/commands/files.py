"""File group management commands."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.config import load_config, save_config
from notes_vault.models import FileGroup

console = Console()


def add(
    name: Annotated[str, cyclopts.Parameter(help="File group name")],
    path: Annotated[str, cyclopts.Parameter(help="Glob pattern for file paths")],
    sensitivity: Annotated[str, cyclopts.Parameter(help="Default sensitivity level")],
):
    """Add a new file group."""
    config = load_config()

    if name in config.files:
        console.print(f"[red]Error:[/red] File group '{name}' already exists")
        return

    config.files[name] = FileGroup(name=name, path=path, sensitivity=sensitivity)
    save_config(config)

    console.print(f"[green]✓[/green] File group '{name}' added")
    console.print(f"  Path: {path}")
    console.print(f"  Sensitivity: {sensitivity}")


def list_files():
    """List all file groups."""
    config = load_config()

    if not config.files:
        console.print("[yellow]No file groups configured[/yellow]")
        return

    table = Table(title="File Groups")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="blue")
    table.add_column("Sensitivity", style="green")

    for name, file_group in config.files.items():
        table.add_row(name, file_group.path, file_group.sensitivity)

    console.print(table)


def update(
    name: Annotated[str, cyclopts.Parameter(help="File group name")],
    path: Annotated[str | None, cyclopts.Parameter(help="New glob pattern")] = None,
    sensitivity: Annotated[str | None, cyclopts.Parameter(help="New sensitivity level")] = None,
):
    """Update an existing file group."""
    config = load_config()

    if name not in config.files:
        console.print(f"[red]Error:[/red] File group '{name}' not found")
        return

    if path:
        config.files[name].path = path
    if sensitivity:
        config.files[name].sensitivity = sensitivity

    save_config(config)
    console.print(f"[green]✓[/green] File group '{name}' updated")


def delete(
    name: Annotated[str, cyclopts.Parameter(help="File group name")],
):
    """Delete a file group."""
    config = load_config()

    if name not in config.files:
        console.print(f"[red]Error:[/red] File group '{name}' not found")
        return

    del config.files[name]
    save_config(config)
    console.print(f"[green]✓[/green] File group '{name}' deleted")
