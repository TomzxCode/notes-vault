# Notes Vault

A privacy-sensitive notes sync CLI tool with regex-based access control.

## Overview

Notes Vault (`notes-vault` or `nv`) exports your notes to consumer-specific directories based on content matching rules. Each consumer (e.g. an LLM, a work assistant) gets its own target directory containing only the notes it is allowed to see. Access is controlled by configurable regex patterns matched against file content.

## Features

- **Regex-based filtering**: Include or exclude files based on regex patterns matched against file content
- **Path exclusions**: Skip files by glob patterns matched against their paths
- **Consumer directories**: Each consumer gets a clean export of only its matching notes
- **Optional UUID renaming**: Rename exported files to deterministic UUIDs to hide filenames from consumers
- **Directory structure preservation**: Exported files maintain their original directory hierarchy
- **Parallel scanning**: Multi-threaded file discovery and export for large vaults
- **File group management**: Organize source notes using glob patterns
- **YAML configuration**: Human-readable, hand-editable configuration

## Installation

```bash
uv tool install https://github.com/TomzxCode/notes-vault.git
```

## Quick Start

### 1. Add File Groups

```bash
# Add a file group pointing to your notes
nv files add mynotes --path "~/Documents/notes/**/*.md"
```

### 2. Add Consumers

```bash
# A work assistant that sees notes tagged #work, but not #private
nv consumers add work-assistant \
  --target "~/exports/work" \
  --include-queries "#work" \
  --exclude-queries "#private"

# A personal assistant with access to all notes, files renamed to UUIDs
nv consumers add claude \
  --target "~/exports/claude" \
  --rename
```

### 3. Sync

```bash
# Sync all consumers
nv sync

# Sync a specific consumer
nv sync claude

# Sync with explicit parallelism
nv sync --workers 8
```

Each sync deletes and recreates the target directory with the current matching files.

## Configuration

Stored at `~/.config/notes-vault/config.yaml` (or `$XDG_CONFIG_HOME/notes-vault/config.yaml`).

```yaml
files:
  my-notes:
    path: "~/Documents/notes/**/*.md"

consumers:
  claude:
    name: claude
    target: "~/exports/claude"
    include_queries: []
    exclude_queries: []
    exclude_paths: []
    rename: true
  work-assistant:
    name: work-assistant
    target: "~/exports/work"
    include_queries:
      - "#work"
    exclude_queries:
      - "#private"
    exclude_paths:
      - "*/drafts/*"
    rename: false
```

## How It Works

### File Matching

For each file discovered from the configured file groups, the syncer applies the following checks in order:

1. **Path exclusion**: if the file path matches any `exclude_paths` glob, the file is skipped
2. **Content exclusion**: if the file content matches any `exclude_queries` regex, the file is skipped
3. **Content inclusion**: if `include_queries` is non-empty and the content does not match any pattern, the file is skipped
4. Files passing all checks are copied to the consumer's target directory

### Directory Structure

When `rename` is false, exported files preserve their original directory structure relative to the file group's base path. When `rename` is true, files are renamed using a deterministic UUID5 derived from the absolute file path - the same file always gets the same UUID across syncs.

### Sync Behaviour

`nv sync` deletes the target directory and recreates it from scratch on every run. There is no incremental update or state tracking.

## CLI Commands

### Sync

```bash
nv sync                      # sync all consumers
nv sync <consumer>           # sync one consumer
nv sync --workers <n>        # sync with explicit worker count
```

### File Group Management

```bash
nv files add <name> --path <glob>
nv files list
nv files update <name> [--path <glob>]
nv files delete <name>
```

### Consumer Management

```bash
nv consumers add <name> \
  --target <dir> \
  [--include-queries <pattern1,pattern2,...>] \
  [--exclude-queries <pattern1,pattern2,...>] \
  [--exclude-paths <glob1,glob2,...>] \
  [--rename]

nv consumers list
nv consumers update <name> [--target <dir>] [--include-queries <...>] [--exclude-queries <...>] [--exclude-paths <...>] [--rename/--no-rename]
nv consumers delete <name>
```

## Development

```bash
# Run all tests
uv run pytest -v

# Lint and format
uv run ruff check src tests
uv run ruff format src tests
```

## Architecture

- **models.py**: Pydantic data models (`FileGroup`, `Consumer`, `Config`)
- **config.py**: YAML configuration management
- **syncer.py**: File discovery, regex/glob matching, and parallel export
- **cli.py**: CLI entry point (Cyclopts)
- **commands/**: CLI command implementations

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
