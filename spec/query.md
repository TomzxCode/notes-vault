# Query

## Overview

The `query` command performs full-text search across notes accessible to an API key. It delegates the actual text search to `ripgrep` (`rg`), passing only the file paths the key is permitted to access. Results are returned with match context or as a list of UUIDs.

## Requirements

### Access Enforcement

- The system MUST only search files that the requesting API key has permission to access.
- The system MUST resolve accessible files by running access control checks before invoking ripgrep.
- The system MUST NOT pass inaccessible file paths to ripgrep.

### Search Execution

- The system MUST use `ripgrep` (`rg`) as the search backend.
- The system MUST require `ripgrep` to be installed on the system; the command MUST fail with a clear error if `rg` is not found.
- The system MUST invoke ripgrep with `--json` output format to parse results programmatically.
- The system MUST pass the list of accessible file paths directly to ripgrep rather than directory paths, to ensure access control is respected.
- The system MUST perform case-insensitive search by default.
- The system MUST support case-sensitive search via the `--case-sensitive` flag.

### Output

- By default, the system MUST output matching lines with their source note UUID and line number.
- When `--files-only` is specified, the system MUST output only the UUIDs of notes that contain at least one match, with no line content.
- The system MUST map file paths back to UUIDs for all output, so that consumers see UUIDs rather than raw file paths.
- The system MAY include match context (surrounding lines) when requested.

### Error Handling

- The system MUST return a non-zero exit code if ripgrep is not installed.
- The system MUST handle the case where no accessible notes exist and return an empty result.
- The system MUST handle the case where ripgrep finds no matches and return an empty result without error.

### Logging

- The system MUST log a query access entry to the audit log upon invocation.

## Behavior

### Query Execution

1. Resolve the API key and expand its access set.
2. Retrieve all accessible note paths from the index.
3. If no accessible notes exist, return empty results.
4. Construct the ripgrep command:
   - `rg --json [--case-sensitive] <pattern> <path1> <path2> ...`
5. Execute ripgrep and capture stdout.
6. Parse JSON output lines; each line is a ripgrep event (match, begin, end, summary).
7. For each match event, resolve the file path to a UUID using the index.
8. Aggregate results by UUID.

### Output Modes

**Default (line matches):**
```
<uuid>  <line-number>  <matched-line-content>
```

**Files only (`--files-only`):**
```
<uuid>
<uuid>
```

## Dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ripgrep` (`rg`) | Yes | System package; not installed by pip/uv |

## CLI

```bash
nv query --api-key <key> <pattern> [--case-sensitive] [--files-only]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--api-key KEY` | (or `NOTES_VAULT_KEY` env var) | Raw API key |
| `--case-sensitive` | False | Enable case-sensitive matching |
| `--files-only` | False | Output only UUIDs of matching notes |

## Example

```bash
# Find notes containing "meeting agenda"
nv query --api-key $MY_KEY "meeting agenda"

# Case-sensitive search for a specific tag
nv query --api-key $MY_KEY "TODO" --case-sensitive

# Get only the UUIDs of notes mentioning "project alpha"
nv query --api-key $MY_KEY "project alpha" --files-only
```
