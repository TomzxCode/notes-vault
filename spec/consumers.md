# Consumers

## Overview

Consumers are named export destinations. Each consumer defines a target directory and regex query rules that determine which files it receives. During sync, matching files are copied into the consumer's target directory.

## Requirements

### Creation

- The system MUST reject creation if a consumer with the same name already exists.
- The system MUST require a target directory path when creating a consumer.
- The system MUST persist the new consumer to `config.yaml` immediately.

### Listing

- The system MUST display all configured consumers with their names, target directories, include queries, exclude queries, exclude paths, and rename flag.

### Update

- The system MUST allow updating a consumer's target, include_queries, exclude_queries, exclude_paths, and rename flag independently.
- The system MUST persist changes to `config.yaml` immediately.

### Deletion

- The system MUST remove the consumer entry from `config.yaml` on deletion.
- Deletion MUST NOT delete the consumer's target directory.

### UUID Renaming

- When `rename: true`, exported files MUST be renamed to `<uuid5><extension>`.
- The UUID MUST be derived from the absolute file path using UUID5 with `NAMESPACE_URL`.
- The UUID MUST be deterministic: the same source file always produces the same UUID across syncs.
- When `rename: false`, files are copied with their original filename.
- When filenames collide (rename: false), the system MUST append a numeric suffix (e.g., `note_1.md`) to avoid overwrites.

## Data Model

```
Consumer:
  name: str                  # Unique human-readable name
  target: str                # Target directory path (supports ~)
  include_queries: list[str] # Regex patterns; at least one must match for export
  exclude_queries: list[str] # Regex patterns; any match prevents export
  exclude_paths: list[str]   # Glob patterns; any match on the file path prevents export
  rename: bool               # Whether to rename exported files to UUIDs
```

## Behavior

### Add

1. Validate the name is not already in use.
2. Parse include_queries, exclude_queries, and exclude_paths from comma-separated strings into lists.
3. Create `Consumer` with target, include_queries, exclude_queries, exclude_paths, and rename flag.
4. Write updated config.
5. Print confirmation.

### List

1. Load config.
2. Print each consumer's name, target, include_queries, exclude_queries, exclude_paths, and rename flag in a table.

### Update

1. Validate the consumer exists.
2. Apply any provided changes (target, include_queries, exclude_queries, exclude_paths, rename).
3. Write updated config.

### Delete

1. Validate the consumer exists.
2. Remove the entry from config.
3. Write updated config.

## CLI Commands

| Command | Description |
|---------|-------------|
| `nv consumers add <name> <target> [--include-queries] [--exclude-queries] [--exclude-paths] [--rename]` | Create a new consumer |
| `nv consumers list` | List all consumers |
| `nv consumers update <name> [--target] [--include-queries] [--exclude-queries] [--exclude-paths] [--rename/--no-rename]` | Update a consumer |
| `nv consumers delete <name>` | Delete a consumer |
