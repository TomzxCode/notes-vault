# Configuration

## Overview

Notes Vault stores its settings in a YAML file on disk. The configuration is the source of truth for all sensitivity levels, file groups, and API keys. It is loaded on each command invocation and written back whenever a mutating command completes.

## Requirements

### Config Directory

- The system MUST use `~/.config/notes-vault/` as the default configuration directory.
- The system MUST allow overriding the config directory via the `VAULT_CONFIG_DIR` environment variable.
- The system MUST create the config directory and all intermediate directories if they do not exist.

### Config File

- The configuration MUST be stored in a file named `config.yaml` within the config directory.
- The system MUST create an empty (default) config file if one does not exist at startup.
- The system MUST parse the config file using PyYAML and validate it with Pydantic models.
- The system MUST write the config file atomically to avoid partial writes on failure.
- The config file SHOULD be human-readable and directly editable with a text editor.

### Database File

- The SQLite index MUST be stored in a file named `index.db` within the config directory.
- The system MUST create the database and required tables on first use.

### Access Log File

- The access log MUST be stored in a file named `access.log` within the config directory.
- The access log MUST be opened in append mode.

### Default Settings

- The system MUST support a `defaults.sensitivity` setting that specifies the fallback sensitivity level for notes that match no hashtag pattern.
- The `defaults.sensitivity` value SHOULD reference an existing sensitivity level name.
- The system MUST allow setting `defaults.sensitivity` via `nv defaults --sensitivity <level>`.

### Serialization

- The system MUST serialize `set` fields (e.g., `includes`, `sensitivities`) as YAML lists.
- The system MUST deserialize YAML lists back into `set` fields.
- The system MUST preserve all fields during a load-modify-save round trip without data loss.

## Data Model

```
Config:
  defaults:
    sensitivity: str                        # Global fallback sensitivity level name

  files: dict[str, FileGroup]              # Keyed by group name
  keys: dict[str, ApiKey]                  # Keyed by key name
  sensitivities: dict[str, SensitivityLevel]  # Keyed by level name
```

## File Layout

```
$VAULT_CONFIG_DIR/       (default: ~/.config/notes-vault/)
├── config.yaml          # YAML configuration (human-readable)
├── index.db             # SQLite note metadata index
└── access.log           # Append-only access audit log
```

## Behavior

### Load

1. Resolve config directory (`VAULT_CONFIG_DIR` or `~/.config/notes-vault/`).
2. If `config.yaml` does not exist, return a default empty `Config`.
3. Parse YAML into a plain dict.
4. Construct nested Pydantic models from the dict.
5. Return the `Config` object.

### Save

1. Serialize the `Config` object to a plain dict (converting sets to sorted lists).
2. Render the dict to YAML.
3. Write to `config.yaml` (overwrite).

## Config File Example

```yaml
defaults:
  sensitivity: private

files:
  personal:
    path: ~/notes/**/*.md
    sensitivity: private

keys:
  admin_key:
    key_hash: a3f5b2c1...
    sensitivities:
      - private

sensitivities:
  private:
    description: Private personal notes
    query: "#private"
    includes:
      - work
      - public
  work:
    description: Work-related notes
    query: "#work"
    includes:
      - public
  public:
    description: Public notes
    query: "#public"
    includes: []
```
