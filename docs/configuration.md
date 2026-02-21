# Configuration

Notes Vault follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/).

**Config file** (`config.yaml`) and **log file** (`access.log`) are stored under:

```
$XDG_CONFIG_HOME/notes-vault/     # defaults to ~/.config/notes-vault/
```

**Database** (`index.db`) is stored under:

```
$XDG_DATA_HOME/notes-vault/       # defaults to ~/.local/share/notes-vault/
```

You can override the defaults by setting the standard XDG environment variables:

```bash
export XDG_CONFIG_HOME=/path/to/config
export XDG_DATA_HOME=/path/to/data
```

## Configuration File Structure

```yaml
defaults:
  sensitivity: "private"        # Fallback sensitivity for unclassified notes

files:
  <group-name>:
    path: "<glob-pattern>"      # Glob pattern to match note files
    sensitivity: "<level>"      # Default sensitivity for this group

keys:
  <key-name>:
    key_hash: "<sha256-hash>"   # SHA-256 hash of the raw API key
    sensitivities:
      - <level>

sensitivities:
  <level-name>:
    description: "<text>"
    query: "<regex>"            # Regex pattern matched against note content
    includes:
      - <other-level>           # Levels this level grants access to
```

## `defaults`

| Field | Type | Description |
|-------|------|-------------|
| `sensitivity` | string | Sensitivity level applied to notes with no matching hashtag |

Example:
```yaml
defaults:
  sensitivity: "private"
```

## `files`

Each entry under `files` defines a file group - a named collection of note files matched by a glob pattern.

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Glob pattern (supports `**` for recursive matching) |
| `sensitivity` | string | Default sensitivity level for notes in this group |

Example:
```yaml
files:
  personal-notes:
    path: "~/notes/personal/**/*.md"
    sensitivity: "private"
  work-notes:
    path: "~/notes/work/**/*.md"
    sensitivity: "work"
```

## `keys`

Each entry under `keys` defines an API key. Raw key values are never stored - only their SHA-256 hash.

| Field | Type | Description |
|-------|------|-------------|
| `key_hash` | string | SHA-256 hash of the raw API key |
| `sensitivities` | list | Sensitivity levels this key can access |

Example:
```yaml
keys:
  admin_key:
    key_hash: "a3f5..."
    sensitivities:
      - private
  public_key:
    key_hash: "b7c2..."
    sensitivities:
      - public
```

!!! warning
    Do not edit `key_hash` manually. Use `nv keys add` / `nv keys update` to manage keys.

## `sensitivities`

Each entry defines a sensitivity level with a hashtag detection pattern.

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable description |
| `query` | string | Regex pattern matched against note content |
| `includes` | list | Other sensitivity levels this level grants access to |

Example:
```yaml
sensitivities:
  private:
    description: "Private personal notes"
    query: "#private"
    includes:
      - work
      - public
  work:
    description: "Work-related notes"
    query: "#work"
    includes:
      - public
  public:
    description: "Public notes"
    query: "#public"
    includes: []
```

### The `query` Field

The `query` field is a regex pattern applied to note content. A note is classified as a given sensitivity level if the pattern matches anywhere in the file.

Simple hashtag examples:
```yaml
query: "#private"       # matches literal "#private"
query: "#(private|confidential)"  # matches either hashtag
query: "^#private$"     # matches only if "#private" is on its own line
```

### The `includes` Field

The `includes` field defines hierarchical access. If key K has access to level A, and A includes level B, then K can also access notes at level B.

This means a key granted `private` access can see all notes, while a key granted `public` access can only see `public` notes.

## Full Example

```yaml
defaults:
  sensitivity: "private"

files:
  personal:
    path: "~/Documents/notes/**/*.md"
    sensitivity: "private"
  journal:
    path: "~/Documents/journal/*.md"
    sensitivity: "private"

keys:
  admin_key:
    key_hash: "sha256_hash_here"
    sensitivities:
      - private
  work_key:
    key_hash: "sha256_hash_here"
    sensitivities:
      - work
  public_key:
    key_hash: "sha256_hash_here"
    sensitivities:
      - public

sensitivities:
  private:
    description: "Private personal notes"
    query: "#private"
    includes:
      - work
      - public
  work:
    description: "Work-related notes"
    query: "#work"
    includes:
      - public
  public:
    description: "Shareable public notes"
    query: "#public"
    includes: []
```
