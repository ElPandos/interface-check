---
title:        System File Header Requirements
inclusion:    always
version:      1.2
last-updated: 2026-01-14 17:32:00
status:       active
---

# File Header Requirements

## Purpose
Ensure all `.md` files have consistent frontmatter for organization and tracking.

## Required Format
```yaml
---
title:        [Descriptive Title]
inclusion:    always
version:      [X.Y]
last-updated: YYYY-MM-DD HH:MM:SS
status:       active
---
```

## Field Definitions
- **title**: Clear, descriptive title
- **inclusion**: "always" for steering documents
- **version**: Semantic version (major.minor)
- **last-updated**: ISO date (YYYY-MM-DD HH:MM:SS)
- **status**: active, draft, or deprecated

## Rules
- Must be at file top
- YAML frontmatter format
- Update version and date when modifying

## Scope
All `.md` files in steering, configuration, and documentation directories.

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Optimized for brevity, removed redundant sections
