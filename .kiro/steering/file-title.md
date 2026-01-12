---
title:        File Title Frontmatter Requirements
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# File Title Frontmatter Requirements

## Purpose
Ensure all `.md` files have consistent frontmatter with proper metadata for organization and tracking.

## Mandatory Behavior
When creating or updating any `.md` file, **MUST** include frontmatter at the top of the file.

## Required Format
```yaml
---
title:        [Descriptive Title]
inclusion:    always
version:      [X.Y]
last-updated: YYYY-MM-DD
status:       active
---
```

## Field Definitions
- **title**: Clear, descriptive title of the document
- **inclusion**: Set to "always" for steering documents
- **version**: Semantic version number (major.minor)
- **last-updated**: ISO date format (YYYY-MM-DD)
- **status**: Document status (active, draft, deprecated)

## Implementation Rules
- **Location**: Must be at the very top of the file
- **Format**: YAML frontmatter between triple dashes
- **Spacing**: Use consistent spacing as shown in example
- **Updates**: Update version and last-updated when modifying content

## Example
```markdown
---
title:        Network Interface Monitoring Guide
inclusion:    always
version:      1.2
last-updated: 2026-01-12
status:       active
---

# Network Interface Monitoring Guide
[Document content follows...]
```

## Scope
Applies to all `.md` files in:
- Steering documents
- Configuration files
- Documentation files
- README files

## Version History

- v1.0 (2026-01-12): Initial version
