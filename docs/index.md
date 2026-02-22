# Notes Vault

**Notes Vault** is a privacy-sensitive notes sync CLI tool with pattern-based access control.

## What is Notes Vault?

Notes Vault (`nv`) exports your notes to consumer-specific directories based on regex query rules. Each consumer (e.g. an LLM assistant, a work tool) gets its own target directory containing only the notes it is allowed to see. Each consumer defines which files it receives using include and exclude patterns matched against file content.

## Key Features

- **Include/exclude queries** - Each consumer specifies regex patterns to include and exclude files by content
- **Consumer directories** - Each consumer gets a clean export of only its matching notes
- **Optional UUID renaming** - Rename exported files to deterministic UUIDs to hide filenames from consumers
- **File group management** - Organize source notes using glob patterns
- **YAML configuration** - Human-readable, hand-editable configuration

## How It Works

```
Notes (markdown files)
        │
        ▼
  File groups (glob patterns) collect files
        │
        ▼
  Query matching: exclude_queries checked first, then include_queries
        │
        ▼
  Matching files copied to consumer target directory
```

## Quick Example

```bash
# Add your notes directory
nv files add mynotes "~/notes/**/*.md"

# Add a consumer - sees all #work notes except #private ones
nv consumers add work-assistant "~/exports/work" \
  --include-queries "#work" \
  --exclude-queries "#private" \
  --rename

# Sync
nv sync
```

## Next Steps

- [Installation](installation.md) - Install Notes Vault
- [Quick Start](quickstart.md) - Get up and running in minutes
- [Concepts](concepts.md) - Understand consumers and sync
- [Configuration](configuration.md) - Full configuration reference
- [CLI Reference](cli.md) - All commands and options
