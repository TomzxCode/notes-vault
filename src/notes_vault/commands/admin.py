"""Admin commands for defaults and indexing."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.config import load_config, save_config
from notes_vault.indexer import index_all
from notes_vault.storage import init_db

console = Console()


def defaults(
    sensitivity: Annotated[
        str | None, cyclopts.Parameter(help="Set default sensitivity level")
    ] = None,
):
    """Show or set default sensitivity level."""
    config = load_config()

    if sensitivity:
        # Set new default
        config.defaults["sensitivity"] = sensitivity
        save_config(config)
        console.print(f"[green]✓[/green] Default sensitivity set to: {sensitivity}")
    else:
        # Show current defaults
        if not config.defaults:
            console.print("[yellow]No defaults configured[/yellow]")
            return

        table = Table(title="Default Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        for key, value in config.defaults.items():
            table.add_row(key, str(value))

        console.print(table)


def index():
    """Manually trigger indexing of all configured file groups."""
    init_db()
    console.print("[cyan]Starting indexing...[/cyan]")

    stats = index_all()

    console.print("\n[green]Indexing complete![/green]")
    console.print(f"  Indexed: {stats['indexed']}")
    console.print(f"  Skipped: {stats['skipped']}")
    console.print(f"  Errors:  {stats['errors']}")
