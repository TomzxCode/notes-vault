"""Admin commands for syncing."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from notes_vault.config import load_config
from notes_vault.syncer import sync_consumer

console = Console()


def sync(
    consumer: Annotated[
        str | None, cyclopts.Parameter(help="Consumer name (sync all if omitted)")
    ] = None,
    workers: Annotated[
        int | None, cyclopts.Parameter(help="Number of parallel workers (default: auto)")
    ] = None,
):
    """Sync notes to consumer target directories."""
    config = load_config()
    consumers = config.consumers

    if consumer:
        if consumer not in consumers:
            console.print(f"[red]Error:[/red] Consumer '{consumer}' not found")
            return
        consumers = {consumer: consumers[consumer]}

    if not consumers:
        console.print("[yellow]No consumers configured[/yellow]")
        return

    for name, c in consumers.items():
        found_count = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[{name}] Scanning...", total=None)

            def on_file_found() -> None:
                nonlocal found_count
                found_count += 1
                progress.update(task, total=found_count)

            def on_progress(current: int, total: int) -> None:
                progress.update(
                    task, description=f"[{name}] Syncing...", completed=current, total=total
                )

            stats = sync_consumer(
                name,
                c,
                config,
                on_file_found=on_file_found,
                progress_callback=on_progress,
                workers=workers,
            )

        console.print(f"  Exported: {stats['exported']}")
        console.print(f"  Skipped:  {stats['skipped']}")
        console.print(f"  Errors:   {stats['errors']}")
