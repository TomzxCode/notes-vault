# Notes Vault

A privacy-sensitive notes management CLI tool with hashtag-based access control.

## Overview

Notes Vault (`notes-vault` or `nv`) is a standalone Python CLI tool that manages notes with sensitivity-based access control using hashtag detection. It allows you to organize your notes into sensitivity levels and control access via API keys.

## Features

- **Hashtag-based sensitivity detection**: Automatically classify notes based on hashtags like `#private`, `#work`, `#public`
- **Flexible access control**: Define API keys with specific sensitivity permissions
- **Hierarchical access**: Sensitivity levels can include other levels (e.g., `private` includes `work` and `public`)
- **File group management**: Organize notes using glob patterns
- **Efficient indexing**: On-demand indexing with incremental updates and progress reporting
- **Full-text search**: Fast SQLite FTS5-powered search across accessible notes
- **SQLite storage**: Note metadata and content indexed for fast querying
- **YAML configuration**: Human-readable configuration files
- **Access logging**: Audit trail for all access attempts

## Installation

```bash
# Install with uv
uv tool install https://github.com/TomzxCode/notes-vault.git
```

## Quick Start

### 1. Configure Sensitivity Levels

```bash
# Define sensitivity levels
nv sensitivities add private --description "Private notes" --query "#private"
nv sensitivities add work --description "Work notes" --query "#work"
nv sensitivities add public --description "Public notes" --query "#public"

# Set up access hierarchy (private includes work and public)
nv sensitivities include private --include-level work
nv sensitivities include private --include-level public
nv sensitivities include work --include-level public
```

### 2. Add File Groups

```bash
# Add a file group pointing to your notes
nv files add mynotes --path "~/Documents/notes/**/*.md" --sensitivity private
```

### 3. Create API Keys

```bash
# Create API keys with different access levels
nv keys add admin_key --sensitivities private
nv keys add work_key --sensitivities work
nv keys add public_key --sensitivities public
```

### 4. Set Defaults

```bash
# Set default sensitivity for files without hashtags
nv defaults --sensitivity private
```

### 5. Index Your Notes

```bash
# Index all configured file groups
nv index
```

### 6. Access Your Notes

```bash
# List accessible notes
nv list --key public_key

# Get a specific note by UUID
nv get --key public_key <uuid>

# Search within accessible notes
nv query --key public_key "search term"

# API key can also be set via environment variable
export NOTES_VAULT_KEY=public_key
nv list
```

## Configuration

Configuration is stored under `~/.config/notes-vault/config.yaml` (XDG: `$XDG_CONFIG_HOME/notes-vault/config.yaml`). The SQLite index and access log are stored under `~/.local/share/notes-vault/`.

### Configuration Structure

```yaml
defaults:
  sensitivity: "private"

files:
  mynotes:
    path: "~/notes/**/*.md"
    sensitivity: "private"

keys:
  admin_key:
    key_hash: "<sha256-hash>"
    sensitivities:
      - private
  work_key:
    key_hash: "<sha256-hash>"
    sensitivities:
      - work

sensitivities:
  private:
    description: "Private notes"
    query: "#private"
    includes:
      - work
      - public
  work:
    description: "Work notes"
    query: "#work"
    includes:
      - public
  public:
    description: "Public notes"
    query: "#public"
    includes: []
```

## CLI Commands

### Admin Commands

```bash
# Show current defaults
nv defaults

# Set default sensitivity
nv defaults --sensitivity private

# Trigger indexing
nv index
```

### File Group Management

```bash
# Add a file group
nv files add <name> --path <glob-pattern> --sensitivity <level>

# List file groups
nv files list

# Update a file group
nv files update <name> --path <new-pattern> --sensitivity <new-level>

# Delete a file group
nv files delete <name>
```

### API Key Management

```bash
# Add an API key
nv keys add <name> --sensitivities <level1>,<level2>,...

# List API keys
nv keys list

# Update an API key
nv keys update <name> --sensitivities <level1>,<level2>,...

# Delete an API key
nv keys delete <name>
```

### Sensitivity Level Management

```bash
# Add a sensitivity level
nv sensitivities add <name> --description <desc> --query <regex>

# List sensitivity levels
nv sensitivities list

# Update a sensitivity level
nv sensitivities update <name> --description <new-desc> --query <new-regex>

# Delete a sensitivity level
nv sensitivities delete <name>

# Add include relationship
nv sensitivities include <name> --include-level <other-level>
```

### User Commands

```bash
# List accessible notes
nv list --key <key-name>

# Get note content
nv get --key <key-name> <uuid>

# Search for content within accessible notes
nv query --key <key-name> <query-string>

# Case-sensitive search
nv query --key <key-name> <query-string> --case-sensitive

# Show match details and line content
nv query --key <key-name> <query-string> --with-context
```

## How It Works

### Sensitivity Detection

1. Notes are scanned for hashtags matching sensitivity query patterns
2. If multiple hashtags found, the most restrictive (highest in the hierarchy) wins
3. If no hashtags found, the file group's default sensitivity is used; if none, the global default applies
4. Detected sensitivities and effective sensitivity are stored in the index

### Access Control

1. API keys have a set of allowed sensitivity levels
2. Access is expanded via `includes` relationships (e.g., `private` includes `work` and `public`)
3. Notes are filtered based on their effective sensitivity
4. All access attempts are logged

### Indexing

- **Manual**: Run `nv index` to scan and update the metadata index
- **Incremental**: Only re-scans files with changed modification times
- **Efficient**: Batch writes and glob-based file discovery
- **Content stored**: Note content is stored in SQLite to power full-text search without ripgrep

## Development

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=notes_vault --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests
```

## Architecture

- **models.py**: Pydantic data models
- **config.py**: YAML configuration management
- **storage.py**: SQLite database layer
- **sensitivity.py**: Hashtag detection logic
- **indexer.py**: File discovery and scanning
- **access_control.py**: Permission checking
- **cli.py**: CLI entry point with Cyclopts
- **commands/**: CLI command implementations

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
