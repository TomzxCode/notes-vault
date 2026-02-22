# Configuration

## Overview

Notes Vault stores its settings in a YAML file on disk. The configuration is the source of truth for all file groups and consumers. It is loaded on each command invocation and written back whenever a mutating command completes.

## Requirements

### Config Directory

- The system MUST use `~/.config/notes-vault/` as the default configuration directory.
- The system MUST allow overriding the config directory via the `XDG_CONFIG_HOME` environment variable (resolved as `$XDG_CONFIG_HOME/notes-vault/`).
- The system MUST create the config directory and all intermediate directories if they do not exist.

### Config File

- The configuration MUST be stored in a file named `config.yaml` within the config directory.
- The system MUST return a default empty `Config` if `config.yaml` does not exist.
- The system MUST parse the config file using PyYAML and validate it with Pydantic models.
- The config file SHOULD be human-readable and directly editable with a text editor.

### Serialization

- The system MUST serialize `list` fields (e.g., `include_queries`, `exclude_queries`) as YAML lists.
- The system MUST preserve all fields during a load-modify-save round trip without data loss.

## Data Model

```
Config:
  files: dict[str, FileGroup]    # Keyed by group name
  consumers: dict[str, Consumer] # Keyed by consumer name
```

## File Layout

```
$XDG_CONFIG_HOME/notes-vault/   (default: ~/.config/notes-vault/)
└── config.yaml                 # YAML configuration (human-readable)
```

## Behavior

### Load

1. Resolve config directory (`XDG_CONFIG_HOME/notes-vault/` or `~/.config/notes-vault/`).
2. If `config.yaml` does not exist, return a default empty `Config`.
3. Parse YAML into a plain dict.
4. Construct nested Pydantic models from the dict.
5. Return the `Config` object.

### Save

1. Serialize the `Config` object to a plain dict.
2. Render the dict to YAML.
3. Write to `config.yaml` (overwrite).

## Config File Example

```yaml
files:
  personal:
    path: ~/notes/**/*.md

consumers:
  work-assistant:
    target: ~/exports/work
    include_queries:
      - "#work"
      - "#project"
    exclude_queries:
      - "#private"
    rename: true
  public-bot:
    target: ~/exports/public
    include_queries:
      - "#public"
    exclude_queries:
      - "#draft"
    rename: false
```
