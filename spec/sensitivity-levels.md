# Sensitivity Levels

## Overview

Sensitivity levels are the named classifications that Notes Vault uses to categorize notes and control access. Each level defines a regex detection pattern and an optional set of lower-privilege levels it grants access to (the `includes` hierarchy).

## Requirements

### Creation

- The system MUST require a unique name, a description, and a regex query pattern when creating a sensitivity level.
- The system MUST reject creation if a level with the same name already exists.
- The system MUST accept any valid Python regex as the query pattern.
- The system MUST persist the new level to `config.yaml` immediately.
- A newly created level MUST have an empty `includes` set.

### Listing

- The system MUST display all configured sensitivity levels with their name, description, query pattern, and includes set.

### Update

- The system MUST allow updating a level's description and/or query pattern independently.
- The system MUST NOT allow renaming a level (name is the stable identifier).
- The system MUST persist changes to `config.yaml` immediately.
- After updating a query pattern, existing index entries will reflect the old pattern until `nv index` is re-run.

### Deletion

- The system MUST remove the sensitivity level from `config.yaml` on deletion.
- The system SHOULD warn if the level is referenced by any file groups, API keys, or other levels' `includes` sets.
- The system MAY leave dangling references in config; the operator is responsible for cleaning them up.

### Include Relationships

- The system MUST allow adding an include relationship between two existing sensitivity levels.
- The system MUST reject an include if either the source or target level does not exist.
- The system MUST reject an include relationship that would create a cycle (direct or transitive).
- The `includes` set MUST be stored as a list of level names on the source level.
- A level MAY include multiple other levels.
- Include relationships are directional: A includes B does not imply B includes A.

## Data Model

```
SensitivityLevel:
  name: str          # Unique identifier; used in file groups, API keys, and includes
  description: str   # Human-readable label
  query: str         # Python regex pattern matched against note content
  includes: set[str] # Names of levels this level grants access to
```

## Behavior

### Add

1. Validate the name is not already in use.
2. Create the `SensitivityLevel` with an empty `includes` set.
3. Write updated config.

### List

1. Load config.
2. Print each level's name, description, query, and includes in a table.

### Update

1. Validate the level exists.
2. Apply provided changes (description and/or query).
3. Write updated config.

### Delete

1. Validate the level exists.
2. Remove the entry from config.
3. Write updated config.

### Include

1. Validate that both the source and target levels exist.
2. Validate that adding this relationship would not create a cycle.
3. Add the target name to the source level's `includes` set.
4. Write updated config.

## CLI Commands

| Command | Description |
|---------|-------------|
| `nv sensitivities add <name> --description <text> --query <regex>` | Create a level |
| `nv sensitivities list` | List all levels |
| `nv sensitivities update <name> [--description <text>] [--query <regex>]` | Update a level |
| `nv sensitivities delete <name>` | Delete a level |
| `nv sensitivities include <name> --include-level <other>` | Add an include relationship |
