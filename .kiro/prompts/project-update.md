---
title:        Project Update Automation
inclusion:    always
version:      1.5
last-updated: 2026-01-12
status:       active
---

# Project Update Automation

Execute the following commands to update all steering documents:

```bash
# Get current steering prefixes and run research scripts
cd /home/emvekta/_PROJECTS/interface-check

# Extract topics "$TOPICS" variable
source ./scripts/extract_topics.sh

# Update best practices
uv run scripts/research-steering/research.py -m best-practices -t "$TOPICS"

# Update patterns  
uv run scripts/research-steering/research.py -m patterns -t "$TOPICS"

# Update analyze documents
uv run scripts/research-steering/research.py -m analyze -t "$TOPICS"
```

This will automatically refresh all steering documents with the latest research and best practices.

## Version History

- v1.0 (2026-01-12): Initial version
- v1.1 (2026-01-12): Updated to reference project-current.md prompt
- v1.4 (2026-01-12): Added missing analyze type to research commands
- v1.5 (2026-01-12): Renamed PREFIXES variable to PROMPTS for clarity
- v1.6 (2026-01-12): Updated research script arguments from --prompt to --topics
- v1.7 (2026-01-12): Updated script path and arguments to match actual research.py interface
