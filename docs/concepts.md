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

### Union-Based Access Control

A note is accessible to an API key if **any** of its detected sensitivities matches the key's accessible sensitivities.

For example, a note with `#llm` and `#private` tags is accessible to:
- A key with `llm` access (via the `llm` tag)
- A key with `private` access (via the `private` tag)
- Any key that has access to either sensitivity level

This allows notes with multiple sensitivity tags to be accessed by multiple different consumers, each via their appropriate access level.

### Default Sensitivity

If a note matches no sensitivity levels, the file group's default sensitivity is added as a detected sensitivity. This ensures that every note has at least one sensitivity level for access control purposes.

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
- A **sensitivity** - the default sensitivity for notes in this group that match no hashtag

File groups allow you to organize notes from different directories while applying appropriate defaults to each.

---

## API Keys

An API key authenticates a consumer of the Notes Vault. Each key has:

- A **name** (e.g., `admin_key`, `assistant_key`)
- A **set of sensitivities** - the levels this key is permitted to access
- A **hashed value** - the raw key is never stored; only its SHA-256 hash is kept in config

When a new key is created with `nv keys add`, the raw key value is printed once. Store it securely - it cannot be recovered.

### Access Expansion

When a key attempts to access notes, its granted sensitivities are expanded via the include relationships. For example, if a key has `{ private }` as its sensitivities and `private` includes `{ work, public }`, the key's expanded access set is `{ private, work, public }`.

A note is accessible to a key if the note's detected sensitivities intersect with the key's expanded access set.

---

## Indexing

The index is a SQLite database that stores metadata and content for each note. Indexing:

1. Discovers files matching each file group's glob pattern
2. Checks modification times - only re-processes files that have changed
3. Reads each changed file and runs sensitivity detection
4. Assigns a UUID to each note (stable across re-indexing)
5. Stores metadata and full content: UUID, file path, file group, detected sensitivities, content hash, timestamps, note text

### Why UUIDs?

Notes are identified by UUID rather than file path. This provides:

- **Privacy** - the `nv list` output shows UUIDs, not paths, so consumers don't see the underlying directory structure
- **Stability** - if you rename a note file, its UUID is preserved on re-index

### Incremental Indexing

The indexer collects all matching files first, then compares modification times against what was recorded last time. Only changed files are re-read and re-indexed. This makes subsequent `nv index` calls fast even for large note collections.

---

## Full-Text Search

`nv query` searches note content using SQLite FTS5. No external tools are required. The FTS5 index is kept in sync with the notes table automatically during indexing.

- **Case-insensitive** (default): uses FTS5 phrase matching
- **Case-sensitive** (`--case-sensitive`): uses SQLite `INSTR` for exact substring matching
- Results are always filtered to notes accessible to the provided API key

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
