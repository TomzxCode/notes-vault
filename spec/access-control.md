# Access Control

## Overview

Access control governs which files a consumer can receive during sync. It is enforced per-file during each sync run by applying the consumer's `exclude_queries` and `include_queries` against file content. There are no API keys, no authentication, and no audit logging.

## Requirements

### Query Matching

- The system MUST check `exclude_queries` before `include_queries`.
- The system MUST skip a file if any `exclude_queries` pattern matches its content.
- The system MUST export a file if at least one `include_queries` pattern matches its content and no `exclude_queries` pattern matched.
- The system MUST skip a file if no `include_queries` pattern matches.
- A consumer with an empty `include_queries` list receives no files.

## Data Model

```
Consumer:
  name: str
  target: str
  include_queries: list[str]  # Regex patterns; at least one must match
  exclude_queries: list[str]  # Regex patterns; any match prevents export
  rename: bool
```

## Behavior

### Access Check per File

1. Check each `exclude_queries` pattern against file content.
2. If any exclude pattern matches, skip the file.
3. Check each `include_queries` pattern against file content.
4. If at least one include pattern matches, export the file.
5. Otherwise, skip the file.

### Query Matching Algorithm

```python
def matches_any(content: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

# Per-file check:
if matches_any(content, consumer.exclude_queries):
    return "skipped"
if not consumer.include_queries or not matches_any(content, consumer.include_queries):
    return "skipped"
return "exported"
```

## Security Properties

- Access control is purely filesystem-based; there are no credentials or secrets.
- Consumers are isolated by directory: each consumer's target directory contains only the files it is permitted to see.
- UUID renaming (`rename: true`) hides original filenames from the consumer.
- No access log is maintained; sync is a stateless operation.
