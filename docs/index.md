# Notes Vault

**Notes Vault** is a privacy-sensitive notes management CLI tool with hashtag-based access control.

## What is Notes Vault?

Notes Vault (`nv`) lets you organize your markdown notes into sensitivity levels and control access via API keys. It automatically classifies notes based on hashtags like `#private`, `#work`, or `#public`, then enforces access permissions when notes are retrieved or searched.

## Key Features

- **Hashtag-based classification** - Notes are automatically classified by scanning for hashtags that match configured sensitivity patterns
- **API key access control** - Each API key grants access to specific sensitivity levels
- **Hierarchical access** - Sensitivity levels can include other levels (e.g., `private` also grants access to `work` and `public` notes)
- **File group management** - Organize notes using glob patterns
- **Incremental indexing** - Only re-scans files that have changed since the last index
- **Full-text search** - SQLite FTS5-powered search across accessible notes, no external tools required
- **SQLite store** - Note metadata and content indexed for fast querying and search
- **YAML configuration** - Human-readable, editable configuration
- **Access logging** - Audit trail of all access attempts

## How It Works

```
Notes (markdown files)
        │
        ▼
  Indexer scans files
        │
        ▼
  Sensitivity detection (hashtag matching)
        │
        ▼
  Metadata stored in SQLite (UUID, sensitivity, group, hash)
        │
        ▼
  API key → access control check → filtered results
```

## Quick Example

```bash
# Set up sensitivity levels
nv sensitivities add private --description "Private notes" --query "#private"
nv sensitivities add public --description "Public notes" --query "#public"
nv sensitivities include private --include-level public

# Add your notes directory
nv files add mynotes --path "~/notes/**/*.md" --sensitivity private

# Create an API key
nv keys add mykey --sensitivities private

# Index and list notes
nv index
nv list --key mykey
```

## Next Steps

- [Installation](installation.md) - Install Notes Vault and its dependencies
- [Quick Start](quickstart.md) - Get up and running in minutes
- [Concepts](concepts.md) - Understand sensitivity levels, access control, and indexing
- [Configuration](configuration.md) - Full configuration reference
- [CLI Reference](cli.md) - All commands and options
