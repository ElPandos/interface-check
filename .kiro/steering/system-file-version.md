---
title:        System File Version History Requirements
inclusion:    always
version:      1.5
last-updated: 2026-01-15 10:07:00
status:       active
---

# System File Version History Requirements

## Purpose
Ensure all updated `.md` files maintain proper version history tracking for accountability and change management.

## Mandatory Behavior
When updating any `.md` file, **MUST**:
1. Increment the `version` field in the frontmatter
2. Update the `last-updated` field in the frontmatter with current timestamp
3. Add a new entry to the "Version History" section at the end of the file

## Required Format
```markdown
## Version History

- v1.0 (YYYY-MM-DD HH:MM:SS): Initial version
- v1.1 (YYYY-MM-DD HH:MM:SS): Brief description of changes
- v1.2 (YYYY-MM-DD HH:MM:SS): Brief description of changes
```

## Implementation Rules
- **Location**: Always at the end of the file, before any final references
- **Version Format**: Use semantic versioning (major.minor)
  - Increment minor (1.0 → 1.1) for: content updates, clarifications, additions
  - Increment major (1.9 → 2.0) for: breaking changes, complete rewrites, structural changes
- **Timestamp Format**: ISO format with time (YYYY-MM-DD HH:MM:SS)
- **Description**: Brief, clear description of what changed (one line)
- **Consistency**: Each version entry must match the frontmatter version at that point in time
- **Chronological Order**: Oldest first, newest last

## Examples
```markdown
## Version History

- v1.0 (2026-01-12 09:00:00): Initial documentation
- v1.1 (2026-01-12 14:30:00): Added error handling section
- v1.2 (2026-01-13 10:15:00): Updated file naming conventions
```

## Scope
Applies to all `.md` files in:
- Documentation directories
- Configuration files
- Steering documents
- README files
- Any markdown file being modified

**Exception**: Files with frontmatter version tracking (like research-output.md) may use their existing version system instead.

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Added exception for frontmatter versioning, added own version history
- v1.2 (2026-01-12 00:00:00): Updated frontmatter to match file-title format
- v1.3 (2026-01-12 00:00:00): Optimized for brevity, removed redundant content
- v1.4 (2026-01-14 17:35:00): Added implementation rules and clarified format requirements
- v1.5 (2026-01-15 10:07:00): Enforced frontmatter updates, semantic versioning rules, and chronological ordering
