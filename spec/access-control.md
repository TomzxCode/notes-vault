# Access Control

## Overview

Access control governs which notes an API key can read. It is enforced at every note retrieval operation by checking if the note's detected sensitivities intersect with the key's expanded access set. Every access attempt is recorded in an audit log.

## Requirements

### Key Resolution

- The system MUST resolve an API key from its raw value by computing its SHA-256 hash and comparing against stored key hashes.
- The system MUST NOT store raw API key values anywhere in configuration or on disk.
- The system MUST return an error if no key matching the provided raw value is found.
- The system MAY also accept the raw key value via the `NOTES_VAULT_KEY` environment variable as an alternative to the `--key` CLI option.

### Permission Checking

- The system MUST expand a key's granted sensitivities via the transitive `includes` closure before checking access (see `sensitivity-detection.md`).
- The system MUST grant access to a note if and only if the note's detected sensitivities intersect with the key's expanded access set.
- The system MUST deny access to notes whose detected sensitivities have no overlap with the expanded access set.
- The system MUST log every access attempt regardless of whether access is granted or denied.

### Audit Logging

- The system MUST record an `AccessLogEntry` for every call to `get` and `query`.
- Each log entry MUST include: timestamp, API key name, action performed, note UUID, and whether access was granted.
- The audit log MUST be append-only.
- The audit log file MUST be stored at `$VAULT_CONFIG_DIR/access.log`.

### Listing

- The system MUST filter the note index to return only notes whose detected sensitivities intersect with the key's expanded access set when listing notes.
- The `list` command MUST NOT log individual access per note; it MAY log a single list action.

## Data Model

```
ApiKey:
  key_name: str          # Unique name
  key_hash: str          # SHA-256 hex digest of the raw key
  sensitivities: set[str]  # Directly granted sensitivity level names

AccessLogEntry:
  timestamp: datetime    # UTC timestamp of the access attempt
  api_key: str           # Key name used
  action: str            # Action performed (e.g., "get", "query")
  note_uuid: str | None  # UUID of the accessed note (if applicable)
  granted: bool          # Whether access was granted
```

## Behavior

### Key Resolution

1. Compute SHA-256 hash of the supplied raw key string.
2. Iterate all configured `ApiKey` entries; return the first whose `key_hash` matches.
3. If no match found, raise an authentication error.

### Access Check for `get`

1. Resolve the API key.
2. Expand the key's sensitivities via includes closure.
3. Retrieve the note by UUID from the index.
4. If the note's detected sensitivities intersect with the expanded access set, return the note content and log `granted=True`.
5. Otherwise log `granted=False` and raise an authorization error.

### Access Check for `list`

1. Resolve the API key.
2. Expand the key's sensitivities.
3. Query the index for all notes whose detected sensitivities intersect with the expanded set.
4. Return the filtered list without per-note audit logging.

### Access Check for `query`

1. Resolve the API key.
2. Expand the key's sensitivities.
3. Retrieve all accessible notes via the list operation.
4. Collect all detected sensitivities from accessible notes.
5. Search the SQLite FTS5 index filtered to those detected sensitivities.
6. Log a query access entry.

## Security Properties

- Raw API keys are never persisted; only their SHA-256 hashes are stored.
- Access cannot be escalated by modifying the config without also knowing a valid raw key.
- The audit log provides a tamper-evident record of all access attempts (append-only, outside normal config).
