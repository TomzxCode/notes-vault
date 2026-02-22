"""Consumer management commands."""

from typing import Annotated

import cyclopts
from rich.console import Console
from rich.table import Table

from notes_vault.config import load_config, save_config
from notes_vault.models import Consumer

console = Console()


def add(
    name: Annotated[str, cyclopts.Parameter(help="Consumer name")],
    target: Annotated[str, cyclopts.Parameter(help="Target directory path")],
    include_queries: Annotated[
        str, cyclopts.Parameter(help="Comma-separated regex patterns to include files")
    ] = "",
    exclude_queries: Annotated[
        str, cyclopts.Parameter(help="Comma-separated regex patterns to exclude files")
    ] = "",
    rename: Annotated[
        bool, cyclopts.Parameter(help="Rename exported files to deterministic UUIDs")
    ] = False,
):
    """Add a new consumer."""
    config = load_config()

    if name in config.consumers:
        console.print(f"[red]Error:[/red] Consumer '{name}' already exists")
        return

    include_list = [q.strip() for q in include_queries.split(",") if q.strip()]
    exclude_list = [q.strip() for q in exclude_queries.split(",") if q.strip()]
    config.consumers[name] = Consumer(
        name=name,
        target=target,
        include_queries=include_list,
        exclude_queries=exclude_list,
        rename=rename,
    )
    save_config(config)

    console.print(f"[green]✓[/green] Consumer '{name}' added")
    console.print(f"  Target:          {target}")
    console.print(f"  Include queries: {', '.join(include_list) or '-'}")
    console.print(f"  Exclude queries: {', '.join(exclude_list) or '-'}")
    console.print(f"  Rename:          {rename}")


def list_consumers():
    """List all consumers."""
    config = load_config()

    if not config.consumers:
        console.print("[yellow]No consumers configured[/yellow]")
        return

    table = Table(title="Consumers")
    table.add_column("Name", style="cyan")
    table.add_column("Target", style="blue")
    table.add_column("Include Queries", style="green")
    table.add_column("Exclude Queries", style="red")
    table.add_column("Rename", style="yellow")

    for name, consumer in config.consumers.items():
        table.add_row(
            name,
            consumer.target,
            ", ".join(consumer.include_queries) or "-",
            ", ".join(consumer.exclude_queries) or "-",
            str(consumer.rename),
        )

    console.print(table)


def update(
    name: Annotated[str, cyclopts.Parameter(help="Consumer name")],
    target: Annotated[str | None, cyclopts.Parameter(help="New target directory")] = None,
    include_queries: Annotated[
        str | None, cyclopts.Parameter(help="Comma-separated regex patterns to include files")
    ] = None,
    exclude_queries: Annotated[
        str | None, cyclopts.Parameter(help="Comma-separated regex patterns to exclude files")
    ] = None,
    rename: Annotated[
        bool | None, cyclopts.Parameter(help="Rename exported files to UUIDs")
    ] = None,
):
    """Update an existing consumer."""
    config = load_config()

    if name not in config.consumers:
        console.print(f"[red]Error:[/red] Consumer '{name}' not found")
        return

    if target:
        config.consumers[name].target = target
    if include_queries is not None:
        config.consumers[name].include_queries = [
            q.strip() for q in include_queries.split(",") if q.strip()
        ]
    if exclude_queries is not None:
        config.consumers[name].exclude_queries = [
            q.strip() for q in exclude_queries.split(",") if q.strip()
        ]
    if rename is not None:
        config.consumers[name].rename = rename

    save_config(config)
    console.print(f"[green]✓[/green] Consumer '{name}' updated")


def delete(
    name: Annotated[str, cyclopts.Parameter(help="Consumer name")],
):
    """Delete a consumer."""
    config = load_config()

    if name not in config.consumers:
        console.print(f"[red]Error:[/red] Consumer '{name}' not found")
        return

    del config.consumers[name]
    save_config(config)
    console.print(f"[green]✓[/green] Consumer '{name}' deleted")
