# API Keys

## Overview

API keys are the authentication credentials that grant access to notes. Each key is associated with a set of sensitivity levels and identified by a name. Raw key values are never stored; only their SHA-256 hashes are persisted.

## Requirements

### Creation

- The system MUST generate a cryptographically random 64-character hexadecimal key when adding a new API key.
- The system MUST print the raw key value to stdout exactly once at creation time.
- The system MUST store only the SHA-256 hash of the raw key; the raw value MUST NOT be stored anywhere.
- The system MUST require at least one sensitivity level when creating a key.
- The system MUST validate that all specified sensitivity levels exist in the configuration.
- The system MUST reject creation if a key with the same name already exists.
- The system MUST persist the new key to `config.yaml` immediately.

### Listing

- The system MUST display all configured API keys with their names and associated sensitivity levels.
- The system MUST NOT display raw key values or hashes in the listing output.

### Update

- The system MUST allow updating a key's sensitivity levels.
- The system MUST validate that all specified sensitivity levels exist.
- The system MUST NOT allow regenerating the raw key value via update; a new key must be created for key rotation.
- The system MUST persist changes to `config.yaml` immediately.

### Deletion

- The system MUST remove the key entry from `config.yaml` on deletion.
- The system MUST reject requests using the deleted key immediately after deletion.

### Key Security

- Raw key values MUST be generated using a cryptographically secure random source.
- The system MUST use SHA-256 for hashing; no other hash algorithm is acceptable.
- The system MUST NOT log raw key values at any log level.

## Data Model

```
ApiKey:
  key_name: str            # Unique human-readable name
  key_hash: str            # SHA-256 hex digest of the raw key
  sensitivities: set[str]  # Names of directly granted sensitivity levels
```

## Behavior

### Add

1. Validate the name is not already in use.
2. Validate all specified sensitivity levels exist.
3. Generate 32 random bytes; encode as 64-character hex string (the raw key).
4. Compute SHA-256 of the raw key.
5. Create `ApiKey` with the hash and sensitivities.
6. Write updated config.
7. Print the raw key to stdout with a warning that it will not be shown again.

### List

1. Load config.
2. Print each key's name and sensitivity set in a table (no hashes, no raw values).

### Update

1. Validate the key exists.
2. If `--sensitivities` is provided, validate all levels exist.
3. Apply changes.
4. Write updated config.

### Delete

1. Validate the key exists.
2. Remove the entry from config.
3. Write updated config.

## Key Rotation

To rotate a key:

1. Create a new key with the same or updated sensitivities: `nv keys add new_key --sensitivities ...`
2. Update any consumers to use the new raw key value.
3. Delete the old key: `nv keys delete old_key`

## CLI Commands

| Command | Description |
|---------|-------------|
| `nv keys add <name> --sensitivities <levels>` | Create a new API key |
| `nv keys list` | List all keys |
| `nv keys update <name> --sensitivities <levels>` | Update key sensitivities |
| `nv keys delete <name>` | Delete a key |
