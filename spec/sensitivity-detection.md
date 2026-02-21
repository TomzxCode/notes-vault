# Sensitivity Detection

## Overview

Sensitivity detection is the process of classifying a note by scanning its content for patterns defined by configured sensitivity levels. The result is a set of detected sensitivities that determines which API keys can access the note.

## Requirements

### Detection

- The system MUST scan note content against every configured sensitivity level's `query` pattern using regex matching.
- The system MUST record all sensitivity levels whose pattern matches the note content as the note's detected sensitivities.
- The system MUST cache compiled regex patterns to avoid recompilation across multiple notes.
- The system SHOULD treat detection as case-insensitive for hashtag matching.
- A note MAY match zero, one, or multiple sensitivity levels.

### Default Sensitivity

- If a note matches zero sensitivity levels, the system MUST add the file group's default sensitivity to the detected sensitivities.
- If the file group has no default sensitivity, the system MUST use the global default from `defaults.sensitivity`.
- This ensures every note has at least one sensitivity level for access control.

### Access Expansion

- The system MUST expand an API key's granted sensitivities transitively via the `includes` relationships defined on each sensitivity level.
- If level A includes level B, and level B includes level C, a key with access to A MUST also have access to B and C.
- The expansion MUST compute the full transitive closure of the includes graph.
- The system MUST NOT allow circular includes to cause infinite loops during expansion.

## Data Model

```
SensitivityLevel:
  name: str          # Unique identifier
  description: str   # Human-readable label
  query: str         # Regex pattern matched against note content
  includes: set[str] # Names of other levels this level grants access to
```

## Behavior

### Detection Algorithm

1. For each configured sensitivity level, compile (or retrieve cached) regex from `query`.
2. Apply each regex to the full note content using `re.search`.
3. Collect all levels with a match as detected sensitivities.
4. If no sensitivities detected, add the file group's default sensitivity (or global default).

### Expansion Algorithm

1. Start with the set of sensitivity names granted to a key.
2. For each level in the set, add all names from its `includes` set.
3. Repeat until no new levels are added (fixed-point iteration).
4. Return the expanded set.

## Examples

### Single hashtag

Note content: `Meeting notes. #work`
Detected: `{work}`

### Multiple hashtags

Note content: `#private #work`
Detected: `{private, work}`
Accessible by: keys with `private` OR `work` access

### No hashtags

Note content: `Shopping list`
Detected: `{private}` (file group default)
Accessible by: keys with `private` access

### Access expansion

Key sensitivities: `{private}`
`private` includes: `{work, public}`
`work` includes: `{public}`
Expanded access: `{private, work, public}`
