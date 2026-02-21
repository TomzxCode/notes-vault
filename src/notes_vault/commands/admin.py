"""Admin commands for defaults and indexing."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn
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

    found_count = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=None)

        def on_file_found() -> None:
            nonlocal found_count
            found_count += 1
            progress.update(task, total=found_count)

        def on_progress(current: int, total: int) -> None:
            progress.update(task, description="Indexing files...", completed=current, total=total)

        stats = index_all(progress_callback=on_progress, on_file_found=on_file_found)

    console.print("\n[green]Indexing complete![/green]")
    console.print(f"  Indexed: {stats['indexed']}")
    console.print(f"  Skipped: {stats['skipped']}")
    console.print(f"  Errors:  {stats['errors']}")
