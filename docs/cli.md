# CLI Reference

Notes Vault is invoked as `nv` (or `notes-vault`). A user-only variant `nvu` (or `notes-vault-user`) exposes only the read commands.

## Global Options

```
nv --help       Show help
nv --version    Show version
```

---

## Admin Commands

### `nv defaults`

Show or set the default sensitivity level applied to notes with no matching hashtag.

```bash
# Show current default
nv defaults

# Set default sensitivity
nv defaults --sensitivity <level>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--sensitivity LEVEL` | Name of the sensitivity level to set as default |

---

### `nv index`

Scan all configured file groups and update the metadata index. Only re-scans files whose modification time has changed.

```bash
nv index
```

---

## File Group Commands

### `nv files add`

Add a new file group.

```bash
nv files add <name> --path <glob-pattern> --sensitivity <level>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Unique name for this file group |

**Options:**

| Option | Description |
|--------|-------------|
| `--path PATTERN` | Glob pattern matching the note files (e.g., `~/notes/**/*.md`) |
| `--sensitivity LEVEL` | Default sensitivity for notes in this group |

**Example:**

```bash
nv files add personal --path "~/Documents/notes/**/*.md" --sensitivity private
```

---

### `nv files list`

List all configured file groups.

```bash
nv files list
```

---

### `nv files update`

Update an existing file group.

```bash
nv files update <name> [--path <glob-pattern>] [--sensitivity <level>]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the file group to update |

**Options:**

| Option | Description |
|--------|-------------|
| `--path PATTERN` | New glob pattern |
| `--sensitivity LEVEL` | New default sensitivity |

---

### `nv files delete`

Delete a file group.

```bash
nv files delete <name>
```

---

## API Key Commands

### `nv keys add`

Create a new API key. The raw key is printed once - store it securely.

```bash
nv keys add <name> --sensitivities <level1>[,<level2>,...]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Unique name for this key |

**Options:**

| Option | Description |
|--------|-------------|
| `--sensitivities LEVELS` | Comma-separated list of sensitivity levels this key can access |

**Example:**

```bash
nv keys add admin_key --sensitivities private
nv keys add work_key --sensitivities work,public
```

---

### `nv keys list`

List all API keys (names and assigned sensitivities, not raw values).

```bash
nv keys list
```

---

### `nv keys update`

Update the sensitivities for an existing key.

```bash
nv keys update <name> [--sensitivities <level1>[,<level2>,...]]
```

---

### `nv keys delete`

Delete an API key.

```bash
nv keys delete <name>
```

---

## Sensitivity Level Commands

### `nv sensitivities add`

Create a new sensitivity level.

```bash
nv sensitivities add <name> --description <text> --query <regex>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Unique name for this sensitivity level |

**Options:**

| Option | Description |
|--------|-------------|
| `--description TEXT` | Human-readable description |
| `--query REGEX` | Regex pattern matched against note content |

**Example:**

```bash
nv sensitivities add private --description "Private notes" --query "#private"
```

---

### `nv sensitivities list`

List all configured sensitivity levels.

```bash
nv sensitivities list
```

---

### `nv sensitivities update`

Update a sensitivity level's description or query.

```bash
nv sensitivities update <name> [--description <text>] [--query <regex>]
```

---

### `nv sensitivities delete`

Delete a sensitivity level.

```bash
nv sensitivities delete <name>
```

---

### `nv sensitivities include`

Add an include relationship between two sensitivity levels. After this, a key with access to `<name>` will also be able to access notes at `<other-level>`.

```bash
nv sensitivities include <name> --include-level <other-level>
```

**Example:**

```bash
# private includes work (private key can see work notes)
nv sensitivities include private --include-level work
```

---

## User Commands

These commands are also available via the `nvu` / `notes-vault-user` entry points.

### `nv list`

List notes accessible to the given API key.

```bash
nv list --key <raw-key>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--key KEY` | Raw API key value (or set `NOTES_VAULT_KEY` env var instead) |

Output columns: UUID, sensitivity, file group.

---

### `nv get`

Print the content of a note to stdout.

```bash
nv get --key <raw-key> <uuid>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `uuid` | UUID of the note to retrieve |

**Options:**

| Option | Description |
|--------|-------------|
| `--key KEY` | Raw API key value (or set `NOTES_VAULT_KEY` env var) |

---

### `nv query`

Search note content using SQLite FTS5. Only searches notes accessible to the given key.

```bash
nv query --key <raw-key> <search-string> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `search-string` | Text or pattern to search for |

**Options:**

| Option | Description |
|--------|-------------|
| `--key KEY` | Raw API key value (or set `NOTES_VAULT_KEY` env var) |
| `--case-sensitive` | Enable case-sensitive matching (default: case-insensitive) |
| `--with-context` | Show match details and line content (default: print only UUIDs) |

**Examples:**

```bash
# Search for "meeting" in accessible notes (prints matching UUIDs)
nv query --key mykey "meeting"

# Case-sensitive search
nv query --key mykey "TODO" --case-sensitive

# Show match details including line content
nv query --key mykey "project alpha" --with-context
```
