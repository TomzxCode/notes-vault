"""CLI entry point for notes-vault."""

import logging
import sys

import cyclopts
import structlog
from rich.console import Console

from notes_vault.commands import admin, consumers, files

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

console = Console()
app = cyclopts.App(name="notes-vault", help="Privacy-sensitive notes sync CLI")

app.command(admin.sync, name="sync")

files_app = cyclopts.App(name="files", help="Manage file groups")
app.command(files_app)
files_app.command(files.add, name="add")
files_app.command(files.list_files, name="list")
files_app.command(files.update, name="update")
files_app.command(files.delete, name="delete")

consumers_app = cyclopts.App(name="consumers", help="Manage consumers")
app.command(consumers_app)
consumers_app.command(consumers.add, name="add")
consumers_app.command(consumers.list_consumers, name="list")
consumers_app.command(consumers.update, name="update")
consumers_app.command(consumers.delete, name="delete")


def main():
    """Main entry point."""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
