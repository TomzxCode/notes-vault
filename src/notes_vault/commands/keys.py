"""API key management commands."""

import hashlib
import secrets
from typing import Annotated

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.config import load_config, save_config
from notes_vault.models import ApiKey

console = Console()


def add(
    name: Annotated[str, cyclopts.Parameter(help="API key name")],
    sensitivities: Annotated[str, cyclopts.Parameter(help="Comma-separated sensitivity levels")],
):
    """Add a new API key."""
    config = load_config()

    if name in config.keys:
        console.print(f"[red]Error:[/red] API key '{name}' already exists")
        return

    sens_set = set(s.strip() for s in sensitivities.split(","))
    key = secrets.token_hex(32)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    config.keys[name] = ApiKey(key_name=name, key_hash=key_hash, sensitivities=sens_set)
    save_config(config)

    console.print(f"[green]✓[/green] API key '{name}' added")
    console.print(f"  Key:           [bold yellow]{key}[/bold yellow]")
    console.print(f"  Sensitivities: {', '.join(sorted(sens_set))}")
    console.print("\n[dim]Save the key above - it will not be shown again.[/dim]")


def list_keys():
    """List all API keys."""
    config = load_config()

    if not config.keys:
        console.print("[yellow]No API keys configured[/yellow]")
        return

    table = Table(title="API Keys")
    table.add_column("Name", style="cyan")
    table.add_column("Sensitivities", style="green")

    for name, key in config.keys.items():
        table.add_row(name, ", ".join(sorted(key.sensitivities)))

    console.print(table)


def update(
    name: Annotated[str, cyclopts.Parameter(help="API key name")],
    sensitivities: Annotated[
        str | None, cyclopts.Parameter(help="Comma-separated sensitivity levels")
    ] = None,
):
    """Update an existing API key."""
    config = load_config()

    if name not in config.keys:
        console.print(f"[red]Error:[/red] API key '{name}' not found")
        return

    if sensitivities:
        sens_set = set(s.strip() for s in sensitivities.split(","))
        config.keys[name].sensitivities = sens_set

    save_config(config)
    console.print(f"[green]✓[/green] API key '{name}' updated")


def delete(
    name: Annotated[str, cyclopts.Parameter(help="API key name")],
):
    """Delete an API key."""
    config = load_config()

    if name not in config.keys:
        console.print(f"[red]Error:[/red] API key '{name}' not found")
        return

    del config.keys[name]
    save_config(config)
    console.print(f"[green]✓[/green] API key '{name}' deleted")
