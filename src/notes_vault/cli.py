"""CLI entry point for notes-vault."""

import logging
import sys

import cyclopts
import structlog
from rich.console import Console

from notes_vault.commands import admin, files, keys, sensitivity, user

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
app = cyclopts.App(name="notes-vault", help="Privacy-sensitive notes management CLI")


# Register command groups
app.command(admin.defaults, name="defaults")
app.command(admin.index, name="index")

files_app = cyclopts.App(name="files", help="Manage file groups")
app.command(files_app)
files_app.command(files.add, name="add")
files_app.command(files.list_files, name="list")
files_app.command(files.update, name="update")
files_app.command(files.delete, name="delete")

keys_app = cyclopts.App(name="keys", help="Manage API keys")
app.command(keys_app)
keys_app.command(keys.add, name="add")
keys_app.command(keys.list_keys, name="list")
keys_app.command(keys.update, name="update")
keys_app.command(keys.delete, name="delete")

sensitivities_app = cyclopts.App(name="sensitivities", help="Manage sensitivity levels")
app.command(sensitivities_app)
sensitivities_app.command(sensitivity.add, name="add")
sensitivities_app.command(sensitivity.list_sensitivities, name="list")
sensitivities_app.command(sensitivity.update, name="update")
sensitivities_app.command(sensitivity.delete, name="delete")
sensitivities_app.command(sensitivity.include, name="include")

# User commands (top-level)
app.command(user.list_notes, name="list")
app.command(user.get, name="get")
app.command(user.query, name="query")


user_app = cyclopts.App(name="notes-vault-user", help="Notes access CLI")
user_app.command(user.list_notes, name="list")
user_app.command(user.get, name="get")
user_app.command(user.query, name="query")


def main():
    """Main entry point."""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def main_user():
    """User entry point (get, list, query only)."""
    try:
        user_app()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
