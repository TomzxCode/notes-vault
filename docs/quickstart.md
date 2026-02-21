# Quick Start

This guide walks you through setting up Notes Vault from scratch.

## Step 1: Define Sensitivity Levels

Sensitivity levels classify your notes. Each level has a hashtag pattern that is detected in note content.

```bash
# Create three levels: private, work, public
nv sensitivities add private --description "Private personal notes" --query "#private"
nv sensitivities add work --description "Work-related notes" --query "#work"
nv sensitivities add public --description "Public notes" --query "#public"
```

### Set Up Access Hierarchy

Configure which levels grant access to which other levels. Here, a key with `private` access can also see `work` and `public` notes.

```bash
nv sensitivities include private --include-level work
nv sensitivities include private --include-level public
nv sensitivities include work --include-level public
```

## Step 2: Set a Default Sensitivity

Notes without any matching hashtag fall back to the default sensitivity.

```bash
nv defaults --sensitivity private
```

## Step 3: Add File Groups

File groups tell Notes Vault where your notes live. Use glob patterns to match files.

```bash
nv files add mynotes --path "~/Documents/notes/**/*.md" --sensitivity private
```

The `--sensitivity` flag sets the fallback sensitivity for notes in this group that have no matching hashtag.

## Step 4: Create API Keys

API keys authenticate access. Each key is granted one or more sensitivity levels.

```bash
# Full access key (sees private, work, and public notes via hierarchy)
nv keys add admin_key --sensitivities private

# Work key (sees work and public notes)
nv keys add work_key --sensitivities work

# Public key (sees only public notes)
nv keys add public_key --sensitivities public
```

!!! note
    When you create a key, the raw key value is printed once. Store it securely - it cannot be retrieved again.

## Step 5: Index Your Notes

Indexing scans your file groups, detects hashtags, and stores metadata in SQLite.

```bash
nv index
```

Indexing is incremental: subsequent runs only re-scan files that have changed.

## Step 6: Access Your Notes

```bash
# List notes accessible to a key
nv list --key <raw-key-value>

# Get the content of a specific note by its UUID
nv get --key <raw-key-value> <uuid>

# Search notes for a string
nv query --key <raw-key-value> "meeting notes"
```

## Example Note

A note with `#private` in its content:

```markdown
# My Private Note

#private

This note is classified as private because of the hashtag above.
```

A note with both `#work` and `#private`:

```markdown
# Project Alpha

#work #private

Notes about the project...
```

When multiple hashtags are present, the note is accessible to ANY key that has access to ANY of the detected sensitivities. In this example, both `work_key` and `admin_key` could access this note.

## Next Steps

- [Configuration](configuration.md) - Explore all configuration options
- [CLI Reference](cli.md) - Full command reference
- [Concepts](concepts.md) - Deep dive into how sensitivity and access control work
