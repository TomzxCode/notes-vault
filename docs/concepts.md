# Concepts

## File Groups

A file group is a named collection of note files matched by a glob pattern. Each group has:

- A **name** (e.g., `personal`, `work-notes`)
- A **path** - a glob pattern (e.g., `~/notes/**/*.md`)

File groups tell Notes Vault where your notes live. Multiple groups can cover different directories.

---

## Consumers

A consumer is a named destination for synced notes. Each consumer has:

- A **name** (e.g., `claude`, `work-assistant`)
- A **target** - the directory where matching files are exported
- An **include_queries** list - regex patterns matched against file content; at least one must match for the file to be exported
- An **exclude_queries** list - regex patterns matched against file content; any match prevents export regardless of include matches
- A **rename** flag - when `true`, exported files are renamed to deterministic UUIDs

### Matching Logic

For each file, the consumer applies its queries in order:

1. If any `exclude_queries` pattern matches the file content, the file is **skipped**
2. If at least one `include_queries` pattern matches the file content, the file is **exported**
3. Otherwise, the file is **skipped**

Exclude always wins. A file that matches both an exclude and an include query is skipped.

### Empty Query Lists

A consumer with no `include_queries` exports nothing. Use `.*` as an include pattern to match all files.

---

## Sync

`nv sync` exports files to consumer target directories. For each consumer:

1. The target directory is deleted and recreated from scratch
2. All files from configured file groups are collected
3. Each file is read and tested against the consumer's exclude and include queries
4. Files passing the query check are copied to the target
5. If `rename: true`, files are renamed to a deterministic UUID5 derived from the file path

There is no incremental update or state tracking - each sync is a full rebuild of the target directory.

### UUID Renaming

When `rename: true`, exported files are named `<uuid5><extension>` where the UUID is derived from the absolute file path. The same source file always produces the same UUID across syncs, making the mapping stable while hiding the original filename from the consumer.

---

## Storage Layout

```
$XDG_CONFIG_HOME/notes-vault/     (default: ~/.config/notes-vault/)
└── config.yaml                   # YAML configuration

Consumer target directories:
~/exports/claude/                 # example consumer target
~/exports/work-assistant/         # example consumer target
```

The config file is the only persistent state. Consumer target directories are fully managed by `nv sync` and are recreated on every run.
