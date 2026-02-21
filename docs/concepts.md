# Concepts

## Sensitivity Levels

A sensitivity level is a named classification for notes. Each level has:

- A **name** (e.g., `private`, `work`, `public`)
- A **description** for human reference
- A **query** - a regex pattern used to detect the level in note content
- An optional list of **includes** - other levels this level grants access to

### Hashtag Detection

When a note is indexed, its content is scanned against every configured sensitivity level's `query` pattern. Any level whose pattern matches is recorded as a detected sensitivity for that note.

For example, a note containing `#private #work` would have both `private` and `work` as detected sensitivities.

### Effective Sensitivity

If a note matches multiple sensitivity levels, one is chosen as the **effective sensitivity**. The effective sensitivity is determined by which level is highest in the access hierarchy (i.e., the most restrictive).

If a note matches no sensitivity levels, the file group's default sensitivity is used. If there is no group default, the global default from `defaults.sensitivity` is used.

### Include Relationships

Include relationships define a hierarchy between levels. If level A includes level B, then:

- A key with access to A also sees notes at level B
- A note at level B is visible to any key that has A or B in its sensitivities

This allows you to define a natural access pyramid:

```
private → work → public
```

A key with `private` access sees all notes. A key with `work` access sees `work` and `public` notes. A key with `public` access sees only `public` notes.

---

## File Groups

A file group is a named collection of note files matched by a glob pattern. Each group has:

- A **name** (e.g., `personal`, `work-notes`)
- A **path** - a glob pattern (e.g., `~/notes/**/*.md`)
- A **sensitivity** - the fallback sensitivity for notes in this group that match no hashtag

File groups allow you to organize notes from different directories while applying appropriate defaults to each.

---

## API Keys

An API key authenticates a consumer of the Notes Vault. Each key has:

- A **name** (e.g., `admin_key`, `assistant_key`)
- A **set of sensitivities** - the levels this key is permitted to access
- A **hashed value** - the raw key is never stored; only its SHA-256 hash is kept in config

When a new key is created with `nv keys add`, the raw key value is printed once. Store it securely - it cannot be recovered.

### Access Expansion

When a key attempts to access notes, its granted sensitivities are expanded via the include relationships. For example, if a key has `{ private }` as its sensitivities and `private` includes `{ work, public }`, the key's effective access set is `{ private, work, public }`.

A note is accessible to a key if the note's effective sensitivity is within the key's expanded access set.

---

## Indexing

The index is a SQLite database that stores metadata about each note. Indexing:

1. Discovers files matching each file group's glob pattern
2. Checks modification times - only re-processes files that have changed
3. Reads each changed file and runs sensitivity detection
4. Assigns a UUID to each note (stable across renames within a group)
5. Stores metadata: UUID, file path, file group, detected sensitivities, effective sensitivity, content hash, timestamps

### Why UUIDs?

Notes are identified by UUID rather than file path. This provides:

- **Privacy** - the `nv list` output shows UUIDs, not paths, so consumers don't see the underlying directory structure
- **Stability** - if you rename a note file, its UUID is recalculated from content, preserving identity

### Incremental Indexing

The indexer compares the current file modification time against what was recorded last time. Only changed files are re-scanned. This makes subsequent `nv index` calls fast even for large note collections.

---

## Access Logging

Every call to `nv get` and `nv query` generates an access log entry recording:

- Timestamp
- API key used
- Action performed
- Note UUID accessed
- Whether access was granted or denied

The log provides a full audit trail for all note access attempts.

---

## Storage Layout

```
$XDG_CONFIG_HOME/notes-vault/     (default: ~/.config/notes-vault/)
└── config.yaml                   # YAML configuration

$XDG_DATA_HOME/notes-vault/       (default: ~/.local/share/notes-vault/)
├── index.db                      # SQLite metadata index
└── access.log                    # Access audit log
```

The SQLite database is an implementation detail - do not edit it directly. Use `nv index` to rebuild it from the filesystem.
