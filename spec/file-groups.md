# File Groups

## Overview

File groups define named collections of note files matched by a glob pattern. They are the primary mechanism for telling Notes Vault where notes live.

## Requirements

### Creation

- The system MUST require a unique name and a glob path pattern when creating a file group.
- The system MUST reject creation if a file group with the same name already exists.
- The system MUST persist the new file group to `config.yaml` immediately.

### Listing

- The system MUST display all configured file groups, including their name and glob path.

### Update

- The system MUST allow updating a file group's glob path.
- The system MUST persist changes to `config.yaml` immediately.

### Deletion

- The system MUST remove the file group entry from `config.yaml` on deletion.

### Glob Patterns

- The system MUST support standard glob syntax including `*`, `?`, and `[...]`.
- The system MUST support recursive matching via `**`.
- The system MUST resolve `~` to the user's home directory in path patterns.
- The system MAY support environment variable expansion in path patterns.

## Data Model

```
FileGroup:
  name: str  # Unique identifier for the group
  path: str  # Glob pattern matching note files
```

## Behavior

### Add

1. Validate that the name is not already in use.
2. Create the `FileGroup` record.
3. Write updated config to `config.yaml`.

### List

1. Load config.
2. Print each file group's name and path in a table.

### Update

1. Validate that the file group exists.
2. Apply provided changes to the existing record.
3. Write updated config.

### Delete

1. Validate that the file group exists.
2. Remove the entry from the config.
3. Write updated config.

## CLI Commands

| Command | Description |
|---------|-------------|
| `nv files add <name> <path>` | Create a file group |
| `nv files list` | List all file groups |
| `nv files update <name> [--path <glob>]` | Update a file group |
| `nv files delete <name>` | Delete a file group |
