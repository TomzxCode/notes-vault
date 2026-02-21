"""Sensitivity level management commands."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.config import load_config, save_config
from notes_vault.models import SensitivityLevel

console = Console()


def _prompt_index():
    """Prompt user to run index command."""
    console.print("\n[yellow]Hint:[/yellow] Sensitivity levels have changed. Run [cyan]nv index[/cyan] to update the database.")


def add(
    name: Annotated[str, cyclopts.Parameter(help="Sensitivity level name")],
    description: Annotated[str, cyclopts.Parameter(help="Description of this level")],
    query: Annotated[str, cyclopts.Parameter(help="Regex pattern for hashtag detection")],
):
    """Add a new sensitivity level."""
    config = load_config()

    if name in config.sensitivities:
        console.print(f"[red]Error:[/red] Sensitivity level '{name}' already exists")
        return

    config.sensitivities[name] = SensitivityLevel(
        name=name, description=description, query=query, includes=set()
    )
    save_config(config)

    console.print(f"[green]✓[/green] Sensitivity level '{name}' added")
    console.print(f"  Description: {description}")
    console.print(f"  Query: {query}")
    _prompt_index()


def list_sensitivities():
    """List all sensitivity levels."""
    config = load_config()

    if not config.sensitivities:
        console.print("[yellow]No sensitivity levels configured[/yellow]")
        return

    table = Table(title="Sensitivity Levels")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="blue")
    table.add_column("Query", style="yellow")
    table.add_column("Includes", style="green")

    for name, sens in config.sensitivities.items():
        includes_str = ", ".join(sorted(sens.includes)) if sens.includes else "-"
        table.add_row(name, sens.description, sens.query, includes_str)

    console.print(table)


def update(
    name: Annotated[str, cyclopts.Parameter(help="Sensitivity level name")],
    description: Annotated[str | None, cyclopts.Parameter(help="New description")] = None,
    query: Annotated[str | None, cyclopts.Parameter(help="New query pattern")] = None,
):
    """Update an existing sensitivity level."""
    config = load_config()

    if name not in config.sensitivities:
        console.print(f"[red]Error:[/red] Sensitivity level '{name}' not found")
        return

    if description:
        config.sensitivities[name].description = description
    if query:
        config.sensitivities[name].query = query

    save_config(config)
    console.print(f"[green]✓[/green] Sensitivity level '{name}' updated")
    _prompt_index()


def delete(
    name: Annotated[str, cyclopts.Parameter(help="Sensitivity level name")],
):
    """Delete a sensitivity level."""
    config = load_config()

    if name not in config.sensitivities:
        console.print(f"[red]Error:[/red] Sensitivity level '{name}' not found")
        return

    del config.sensitivities[name]
    save_config(config)
    console.print(f"[green]✓[/green] Sensitivity level '{name}' deleted")
    _prompt_index()


def include(
    name: Annotated[str, cyclopts.Parameter(help="Sensitivity level name")],
    include_level: Annotated[str, cyclopts.Parameter(help="Level to include")],
):
    """Add an include relationship to a sensitivity level."""
    config = load_config()

    if name not in config.sensitivities:
        console.print(f"[red]Error:[/red] Sensitivity level '{name}' not found")
        return

    if include_level not in config.sensitivities:
        console.print(f"[red]Error:[/red] Sensitivity level '{include_level}' not found")
        return

    config.sensitivities[name].includes.add(include_level)
    save_config(config)
    console.print(f"[green]✓[/green] '{name}' now includes '{include_level}'")
    _prompt_index()
