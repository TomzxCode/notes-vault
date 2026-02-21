# Development

## Setup

```bash
git clone https://github.com/tomzxcode/notes-vault
cd notes-vault
uv sync
```

This installs all production and development dependencies into a virtual environment managed by uv.

## Project Structure

```
notes-vault/
├── src/notes_vault/
│   ├── __init__.py           # Package init (empty)
│   ├── cli.py                # CLI entry points (Cyclopts)
│   ├── config.py             # YAML config load/save
│   ├── models.py             # Pydantic data models
│   ├── storage.py            # SQLite database layer
│   ├── sensitivity.py        # Hashtag detection logic
│   ├── indexer.py            # File discovery and indexing
│   ├── access_control.py     # Permission checking
│   └── commands/
│       ├── __init__.py
│       ├── admin.py          # defaults, index commands
│       ├── files.py          # file group CRUD
│       ├── keys.py           # API key management
│       ├── sensitivity.py    # sensitivity level management
│       └── user.py           # list, get, query commands
├── tests/
│   ├── conftest.py           # pytest fixtures
│   ├── helpers.py            # test constants
│   ├── test_access_control.py
│   ├── test_config.py
│   ├── test_indexer.py
│   ├── test_models.py
│   ├── test_query.py
│   ├── test_sensitivity.py
│   └── test_storage.py
├── pyproject.toml
└── mkdocs.yml
```

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_access_control.py -v

# Run with coverage report
uv run pytest --cov=notes_vault --cov-report=html
```

## Code Quality

```bash
# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Check formatting without modifying
uv run ruff format --check src tests
```

The project targets Python 3.14 with a line length of 100 characters.

## Documentation

```bash
# Serve docs locally with live reload
uv run mkdocs serve

# Build static docs
uv run mkdocs build
```

## Architecture Overview

### Models (`models.py`)

All data structures are defined as Pydantic models:

- `SensitivityLevel` - name, description, regex query, includes set
- `FileGroup` - name, glob path, default sensitivity
- `ApiKey` - name, SHA-256 hashed key, sensitivities set
- `NoteMetadata` - UUID, path, group, detected/effective sensitivities, timestamps, content hash
- `Config` - top-level config container
- `AccessLogEntry` - timestamp, key, action, UUID, granted flag

### Config (`config.py`)

Loads and saves `config.yaml` using PyYAML. The config directory is resolved via `VAULT_CONFIG_DIR` or defaults to `~/.vault/`.

### Storage (`storage.py`)

Wraps a SQLite database for note metadata. Provides:

- `upsert_note` - insert or update note metadata
- `get_notes` - query notes by sensitivity
- `log_access` - write access log entries

### Sensitivity (`sensitivity.py`)

- `detect_sensitivities` - scans content against all level regex patterns
- `expand_access` - resolves the full set of accessible levels via includes
- `resolve_effective_sensitivity` - picks one sensitivity from a set based on hierarchy

### Indexer (`indexer.py`)

- `index_file_group` - glob-expands a group's path, checks mtimes, scans changed files
- `generate_uuid` - deterministic UUID from content hash
- `compute_hash` - SHA-256 of file content

### Access Control (`access_control.py`)

- `hash_key` - SHA-256 hash of a raw key
- `verify_key` - compare raw key against stored hash
- `check_access` - determine if a key can access a note at a given sensitivity

### CLI (`cli.py`)

Uses [Cyclopts](https://github.com/BrianPugh/cyclopts) for CLI parsing. Two entry points:

- `main()` - full admin + user CLI (`nv`, `nva`, `notes-vault`, `notes-vault-admin`)
- `main_user()` - user-only CLI (`nvu`, `notes-vault-user`)

### Commands (`commands/`)

Each module registers its commands with the Cyclopts app:

- `admin.py` - `defaults`, `index`
- `files.py` - `files add/list/update/delete`
- `keys.py` - `keys add/list/update/delete`
- `sensitivity.py` - `sensitivities add/list/update/delete/include`
- `user.py` - `list`, `get`, `query`

## Dependencies

| Package | Purpose |
|---------|---------|
| `cyclopts` | CLI framework |
| `pydantic` | Data validation and models |
| `pyyaml` | YAML config parsing |
| `rich` | Terminal output formatting |
| `structlog` | Structured logging |

Dev dependencies: `pytest`, `ruff`

External: `ripgrep` (system package, required for `nv query`)

## CI

GitHub Actions runs on every push:

1. `uv sync --all-groups`
2. `ruff check .`
3. `ruff format --check .`
4. `pytest -v`

Documentation is deployed to GitHub Pages on push to `main` via `mkdocs build`.
