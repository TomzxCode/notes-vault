# CLI Reference

Notes Vault is invoked as `nv` (or `notes-vault`).

## Global Options

```
nv --help       Show help
nv --version    Show version
```

---

## Admin Commands

### `nv sync`

Export files to consumer target directories. Deletes and recreates each target directory from scratch.

```bash
# Sync all consumers
nv sync

# Sync a specific consumer
nv sync <consumer>

# Sync with a specific number of parallel workers
nv sync --workers 4
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `consumer` | Consumer name (optional; syncs all consumers if omitted) |

**Options:**

| Option | Description |
|--------|-------------|
| `--workers N` | Number of parallel workers (default: auto) |

**Output:**

For each consumer, prints:
- `Exported` - number of files copied to the target
- `Skipped` - number of files filtered out by query rules
- `Errors` - number of files that failed to read

---

## File Group Commands

### `nv files add`

Add a new file group.

```bash
nv files add <name> <path>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Unique name for this file group |
| `path` | Glob pattern matching the note files (e.g., `~/notes/**/*.md`) |

**Example:**

```bash
nv files add personal "~/Documents/notes/**/*.md"
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
nv files update <name> [--path <glob-pattern>]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the file group to update |

**Options:**

| Option | Description |
|--------|-------------|
| `--path PATTERN` | New glob pattern |

---

### `nv files delete`

Delete a file group.

```bash
nv files delete <name>
```

---

## Consumer Commands

### `nv consumers add`

Add a new consumer.

```bash
nv consumers add <name> <target> [--include-queries <patterns>] [--exclude-queries <patterns>] [--exclude-paths <patterns>] [--rename]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Unique name for this consumer |
| `target` | Target directory path where files will be exported |

**Options:**

| Option | Description |
|--------|-------------|
| `--include-queries PATTERNS` | Comma-separated regex patterns; at least one must match for export |
| `--exclude-queries PATTERNS` | Comma-separated regex patterns; any match prevents export |
| `--exclude-paths PATTERNS` | Comma-separated glob patterns tested against the file path; any match prevents export |
| `--rename` | Rename exported files to deterministic UUIDs (default: false) |

**Example:**

```bash
# Work assistant that sees #work notes but not #private ones
nv consumers add work-assistant "~/exports/work" \
  --include-queries "#work,#project" \
  --exclude-queries "#private" \
  --rename

# Exclude files in an archive folder
nv consumers add public "~/exports/public" \
  --include-queries "#public" \
  --exclude-paths "*/archive/*,*/drafts/*"

# Personal assistant that sees all notes
nv consumers add personal "~/exports/personal" --include-queries ".*"
```

---

### `nv consumers list`

List all configured consumers.

```bash
nv consumers list
```

---

### `nv consumers update`

Update an existing consumer.

```bash
nv consumers update <name> [--target <dir>] [--include-queries <patterns>] [--exclude-queries <patterns>] [--exclude-paths <patterns>] [--rename/--no-rename]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the consumer to update |

**Options:**

| Option | Description |
|--------|-------------|
| `--target DIR` | New target directory |
| `--include-queries PATTERNS` | New comma-separated include patterns (replaces existing) |
| `--exclude-queries PATTERNS` | New comma-separated exclude patterns (replaces existing) |
| `--exclude-paths PATTERNS` | New comma-separated glob path patterns (replaces existing) |
| `--rename / --no-rename` | Enable or disable UUID renaming |

---

### `nv consumers delete`

Delete a consumer.

```bash
nv consumers delete <name>
```
