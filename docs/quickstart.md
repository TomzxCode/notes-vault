# Quick Start

This guide walks you through setting up Notes Vault from scratch.

## Step 1: Add File Groups

File groups tell Notes Vault where your notes live. Use glob patterns to match files.

```bash
nv files add mynotes "~/Documents/notes/**/*.md"
```

## Step 2: Add Consumers

Consumers are the destinations for your synced notes. Each consumer defines which files it receives using include and exclude regex patterns matched against file content.

```bash
# Personal assistant that sees everything
nv consumers add personal "~/exports/personal" --include-queries ".*"

# Work assistant that sees work-tagged notes, excluding private ones
nv consumers add work-assistant "~/exports/work" \
  --include-queries "#work,#project" \
  --exclude-queries "#private" \
  --rename

# Public bot that only sees public notes (excluding drafts)
nv consumers add public-bot "~/exports/public" \
  --include-queries "#public" \
  --exclude-queries "#draft"
```

## Step 3: Sync

Syncing exports matching files to each consumer's target directory.

```bash
# Sync all consumers
nv sync

# Or sync a specific consumer
nv sync work-assistant
```

Each sync deletes and recreates the target directory with the current matching files.

## Example Notes

A note tagged as work:

```markdown
# Project Alpha

#work

Notes about the project...
```

A note tagged as both work and private (excluded from the work consumer):

```markdown
# Salary Discussion

#work #private

This is confidential.
```

A public draft (excluded from the public-bot consumer):

```markdown
# Blog Post Idea

#public #draft

Still working on this...
```

## Next Steps

- [Configuration](configuration.md) - Explore all configuration options
- [CLI Reference](cli.md) - Full command reference
- [Concepts](concepts.md) - Deep dive into how consumers and sync work
