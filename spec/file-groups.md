# File Groups

## Overview

File groups associate a name and default sensitivity with a set of note files matched by a glob pattern. They are the primary mechanism for telling Notes Vault where notes live and what sensitivity to apply when no hashtag is detected.

## Requirements

### Creation

- The system MUST require a unique name, a glob path pattern, and a default sensitivity level when creating a file group.
- The system MUST reject creation if a file group with the same name already exists.
- The system MUST reject creation if the specified default sensitivity level does not exist in the configuration.
- The system MUST persist the new file group to `config.yaml` immediately.

### Listing

- The system MUST display all configured file groups, including their name, glob path, and default sensitivity.

### Update

- The system MUST allow updating a file group's glob path and/or default sensitivity independently.
- The system MUST reject an update if the specified sensitivity level does not exist.
- The system MUST persist changes to `config.yaml` immediately.

### Deletion

- The system MUST remove the file group entry from `config.yaml` on deletion.
- The system SHOULD warn if the deleted group has indexed notes that will become orphaned.
- The system MAY leave existing index entries intact after deletion; they will be pruned on the next `index` run.

### Glob Patterns

- The system MUST support standard glob syntax including `*`, `?`, and `[...]`.
- The system MUST support recursive matching via `**`.
- The system MUST resolve `~` to the user's home directory in path patterns.
- The system MAY support environment variable expansion in path patterns.

## Data Model

```
FileGroup:
  name: str          # Unique identifier for the group
  path: str          # Glob pattern matching note files
  sensitivity: str   # Default sensitivity level for unclassified notes
```

## Behavior

### Add

1. Validate that the name is not already in use.
2. Validate that the sensitivity level exists.
3. Create the `FileGroup` record.
4. Write updated config to `config.yaml`.

### List

1. Load config.
2. Print each file group's name, path, and sensitivity in a table.

### Update

1. Validate that the file group exists.
2. If `--sensitivity` is provided, validate that the level exists.
3. Apply provided changes to the existing record.
4. Write updated config.

### Delete

1. Validate that the file group exists.
2. Remove the entry from the config.
3. Write updated config.

## Relationship to Indexing

File groups drive file discovery during indexing. When `nv index` runs, it expands each group's glob pattern to collect files. The group's `sensitivity` is used as the fallback when a file's content matches no sensitivity level query.

## CLI Commands

| Command | Description |
|---------|-------------|
| `nv files add <name> --path <glob> --sensitivity <level>` | Create a file group |
| `nv files list` | List all file groups |
| `nv files update <name> [--path <glob>] [--sensitivity <level>]` | Update a file group |
| `nv files delete <name>` | Delete a file group |
