# Notes Vault

A privacy-sensitive notes sync CLI tool with pattern-based access control.

## Overview

Notes Vault (`notes-vault` or `nv`) exports your notes to consumer-specific directories based on sensitivity rules. Each consumer (e.g. an LLM, a work assistant) gets its own target directory containing only the notes it is allowed to see. Sensitivity is detected by scanning note content against configurable regex patterns.

## Features

- **Pattern-based sensitivity detection**: Classify notes using regex patterns matched against file content
- **Hierarchical access**: Sensitivity levels can include other levels (e.g. `work` includes `public`)
- **Consumer directories**: Each consumer gets a clean export of only its accessible notes
- **Optional UUID renaming**: Rename exported files to deterministic UUIDs to hide filenames from consumers
- **File group management**: Organize source notes using glob patterns
- **YAML configuration**: Human-readable, hand-editable configuration

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

The `--sensitivity` flag sets the fallback sensitivity for files with no matching patterns.

### 3. Add Consumers

```bash
# A work assistant that can see work and public notes
nv consumers add work-assistant --target "~/exports/work" --sensitivities work

# A personal assistant with full access, files renamed to UUIDs
nv consumers add claude --target "~/exports/claude" --sensitivities private --rename
```

### 4. Sync

```bash
# Sync all consumers
nv sync

# Sync a specific consumer
nv sync claude
```

Each sync deletes and recreates the target directory with the current matching files.

## Configuration

Stored at `~/.config/notes-vault/config.yaml` (or `$XDG_CONFIG_HOME/notes-vault/config.yaml`).

```yaml
defaults:
  sensitivity: private

files:
  mynotes:
    path: "~/Documents/notes/**/*.md"
    sensitivity: private

sensitivities:
  private:
    description: "Private notes"
    query: "#private"
    includes: []
  work:
    description: "Work notes"
    query: "#work"
    includes:
      - public
  public:
    description: "Public notes"
    query: "#public"
    includes: []

consumers:
  claude:
    target: "~/exports/claude"
    sensitivities:
      - private
    rename: true       # optional: rename files to deterministic UUIDs
  work-assistant:
    target: "~/exports/work"
    sensitivities:
      - work
    rename: false
```

## How It Works

### Sensitivity Detection

1. Each file is scanned against the regex `query` patterns defined in `sensitivities`
2. All matching sensitivities are recorded for that file
3. If no patterns match, the file group's `sensitivity` is used; if unset, the global `defaults.sensitivity` applies

### Access Control

A file is exported to a consumer if any of its detected sensitivities intersects with the consumer's allowed set, after expanding via `includes` relationships.

Example: if `work` includes `public`, a consumer with `work` access sees both `#work` and `#public` notes.

### UUID Renaming

When `rename: true`, files are renamed using a deterministic UUID (UUID5) derived from the file path. The same file always gets the same UUID across syncs. This hides filename information from the consumer.

### Sync Behaviour

`nv sync` deletes the target directory and recreates it from scratch on every run. There is no incremental update or state tracking.

## CLI Commands

### Sync

```bash
nv sync              # sync all consumers
nv sync <consumer>   # sync one consumer
```

### File Group Management

```bash
# Add a file group
nv files add <name> --path <glob> --sensitivity <level>
# List file groups
nv files list

# Update a file group
nv files update <name> [--path <glob>] [--sensitivity <level>]

# Delete a file group
nv files delete <name>
```

### Consumer Management

```bash
nv consumers add <name> --target <dir> --sensitivities <level1,level2,...> [--rename]
nv consumers list
nv consumers update <name> [--target <dir>] [--sensitivities <levels>] [--rename/--no-rename]
nv consumers delete <name>
```

### Sensitivity Level Management

```bash
# Add a sensitivity level
nv sensitivities add <name> --description <desc> --query <regex>
# List sensitivity levels
nv sensitivities list

# Update a sensitivity level
nv sensitivities update <name> [--description <desc>] [--query <regex>]

# Delete a sensitivity level
nv sensitivities delete <name>

# Add include relationship
nv sensitivities include <name> --include-level <other>
```

### Defaults

```bash
nv defaults                        # show current default sensitivity
nv defaults --sensitivity <level>  # set default sensitivity
```

## Development

```bash
# Run all tests
uv run pytest -v

# Lint code
uv run ruff check src tests
# Format code
uv run ruff format src tests
```

## Architecture

- **models.py**: Pydantic data models
- **config.py**: YAML configuration management
- **sensitivity.py**: Pattern detection logic
- **syncer.py**: File discovery, sensitivity matching, and export
- **cli.py**: CLI entry point (Cyclopts)
- **commands/**: CLI command implementations

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
