# Query

## Overview

The `query` command performs full-text search across notes accessible to an API key. Search is executed against content stored in the SQLite index using FTS5 (case-insensitive) or `INSTR` (case-sensitive). Results are returned with match context or as a plain list of UUIDs.

## Requirements

### Access Enforcement

- The system MUST only search notes that the requesting API key has permission to access.
- The system MUST resolve accessible notes by running access control checks before searching.
- The system MUST filter FTS results to only those notes whose effective sensitivity is within the key's expanded access set.

### Search Execution

- The system MUST use SQLite FTS5 for case-insensitive search.
- The system MUST use SQLite `INSTR` for case-sensitive search.
- The system MUST perform case-insensitive search by default.
- The system MUST support case-sensitive search via the `--case-sensitive` flag.
- The system MUST NOT require any external tools (e.g., ripgrep) to execute a query.

### Output

- By default, the system MUST output only the UUIDs of notes that contain at least one match.
- When `--with-context` is specified, the system MUST output per-note details including UUID, sensitivity, file group, and matching line numbers with their content.
- The system MUST NOT expose raw file paths in any output.

### Error Handling

- The system MUST handle the case where no accessible notes exist and return an empty result.
- The system MUST handle the case where no matches are found and return an empty result without error.

### Logging

- The system MUST log a query access entry to the audit log upon invocation.

## Behavior

### Query Execution

1. Resolve the API key and expand its access set.
2. Retrieve all notes accessible to the key from the index.
3. If no accessible notes exist, return empty results.
4. Collect the set of effective sensitivity values from the accessible notes.
5. Search the `notes_fts` table (FTS5) or `notes` table (`INSTR`) filtered to those sensitivities.
6. For each matching note, extract matching lines from the stored content.
7. Return results as `(NoteMetadata, [(line_number, line_text)])` tuples.

### Output Modes

**Default (UUIDs only):**
```
<uuid>
<uuid>
```

**With context (`--with-context`):**
```
UUID: <uuid>
Sensitivity: <level>
Group: <group>
Matches: N line(s)
  Line 12: <matched line content>
```

## CLI

```bash
nv query --key <raw-key> <pattern> [--case-sensitive] [--with-context]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--key KEY` | (or `NOTES_VAULT_KEY` env var) | Raw API key |
| `--case-sensitive` | False | Enable case-sensitive matching |
| `--with-context` | False | Show match details including line content |

## Example

```bash
# Find notes containing "meeting agenda" (prints matching UUIDs)
nv query --key $MY_KEY "meeting agenda"

# Case-sensitive search
nv query --key $MY_KEY "TODO" --case-sensitive

# Show match details including line content
nv query --key $MY_KEY "project alpha" --with-context
```
