# Configuration

Notes Vault follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/).

**Config file** (`config.yaml`) is stored under:

```
$XDG_CONFIG_HOME/notes-vault/     # defaults to ~/.config/notes-vault/
```

You can override the default by setting the `XDG_CONFIG_HOME` environment variable:

```bash
export XDG_CONFIG_HOME=/path/to/config
```

## Configuration File Structure

```yaml
files:
  <group-name>:
    path: "<glob-pattern>"      # Glob pattern to match note files

consumers:
  <consumer-name>:
    target: "<directory>"       # Directory where matching files are exported
    include_queries:
      - "<regex>"               # At least one must match for the file to be exported
    exclude_queries:
      - "<regex>"               # Any match prevents export
    rename: false               # Rename exported files to deterministic UUIDs
```

## `files`

Each entry under `files` defines a file group - a named collection of note files matched by a glob pattern.

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Glob pattern (supports `**` for recursive matching) |

Example:
```yaml
files:
  personal-notes:
    path: "~/notes/personal/**/*.md"
  work-notes:
    path: "~/notes/work/**/*.md"
```

## `consumers`

Each entry under `consumers` defines a named export destination.

| Field | Type | Description |
|-------|------|-------------|
| `target` | string | Directory path where matching files are exported |
| `include_queries` | list | Regex patterns; at least one must match for the file to be exported |
| `exclude_queries` | list | Regex patterns; any match prevents export |
| `rename` | boolean | If true, rename exported files to deterministic UUIDs (default: false) |

### Query Patterns

Both `include_queries` and `exclude_queries` accept Python regex patterns matched case-insensitively against the full file content.

```yaml
include_queries:
  - "#public"                   # matches literal "#public"
  - "#(work|project)"          # matches either hashtag
exclude_queries:
  - "#draft"                    # skip files tagged as drafts
  - "#archived"
```

Exclude takes priority: if any `exclude_queries` pattern matches, the file is skipped even if an `include_queries` pattern also matches.

A consumer with an empty `include_queries` list exports nothing.

## Full Example

```yaml
files:
  personal:
    path: "~/Documents/notes/**/*.md"
  journal:
    path: "~/Documents/journal/*.md"

consumers:
  personal-assistant:
    target: "~/exports/personal"
    include_queries:
      - ".*"
    exclude_queries: []
    rename: false
  work-assistant:
    target: "~/exports/work"
    include_queries:
      - "#work"
      - "#project"
    exclude_queries:
      - "#private"
    rename: true
  public-bot:
    target: "~/exports/public"
    include_queries:
      - "#public"
    exclude_queries:
      - "#draft"
    rename: false
```
