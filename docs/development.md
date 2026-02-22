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
│   ├── cli.py                # CLI entry point (Cyclopts)
│   ├── config.py             # YAML config load/save
│   ├── models.py             # Pydantic data models
│   ├── syncer.py             # File discovery, query matching, and export
│   └── commands/
│       ├── __init__.py
│       ├── admin.py          # sync command
│       ├── consumers.py      # consumer CRUD
│       └── files.py          # file group CRUD
├── tests/
│   ├── conftest.py           # pytest fixtures
│   ├── test_config.py
│   ├── test_models.py
│   └── test_syncer.py
├── pyproject.toml
└── mkdocs.yml
```

## Running Tests

```bash
# Run all tests
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_syncer.py -v

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

- `FileGroup` - name and glob path
- `Consumer` - name, target directory, include/exclude query lists, rename flag
- `Config` - top-level config container

### Config (`config.py`)

Loads and saves `config.yaml` using PyYAML. The config directory is resolved via `XDG_CONFIG_HOME` or defaults to `~/.config/notes-vault/`.

### Syncer (`syncer.py`)

- `sync_consumer` - exports files matching a consumer's queries to their target directory
- `sync_all` - syncs all consumers, or just one if a name is specified
- `_collect_files` - discovers all files from configured file groups in parallel
- `_matches_any` - tests content against a list of regex patterns
- `_file_uuid` - generates a deterministic UUID5 from an absolute file path

### CLI (`cli.py`)

Uses [Cyclopts](https://github.com/BrianPugh/cyclopts) for CLI parsing. Single entry point `main()` (`nv`, `notes-vault`).

### Commands (`commands/`)

Each module registers its commands with the Cyclopts app:

- `admin.py` - `sync`
- `consumers.py` - `consumers add/list/update/delete`
- `files.py` - `files add/list/update/delete`

## Dependencies

| Package | Purpose |
|---------|---------|
| `cyclopts` | CLI framework |
| `pydantic` | Data validation and models |
| `pyyaml` | YAML config parsing |
| `rich` | Terminal output formatting |
| `structlog` | Structured logging |

Dev dependencies: `pytest`, `ruff`

## CI

GitHub Actions runs on every push:

1. `uv sync --all-groups`
2. `ruff check .`
3. `ruff format --check .`
4. `pytest -v`

Documentation is deployed to GitHub Pages on push to `main` via `mkdocs build`.
