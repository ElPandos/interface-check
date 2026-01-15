---
title:        Project Update Automation
inclusion:    always
version:      1.8
last-updated: 2026-01-15 15:27:00
status:       active
---

# Project Update Automation

Execute the following commands to update all documentation:

```bash
# Get current topics from docs/ folder
cd /home/emvekta/_PROJECTS/interface-check

# Extract topics into $TOPICS variable
source ./scripts/extract_topics.sh

# Update best practices (parallel with 4 workers)
uv run scripts/research.py -b -p -t "$TOPICS" -w 4 -f

# Update analyze documents (comprehensive web crawling for URLs)
# Example: uv run scripts/research.py -a -t "https://docs.example.com" -d 3 -w 4 -f
```

## New Analyze Mode

The `-a` flag now performs comprehensive web crawling and research:

```bash
# Crawl and research a documentation site
uv run scripts/research.py -a -t "https://kubernetes.io/docs" -d 3 -w 4

# Multiple modes at once
uv run scripts/research.py -a -b -p -t "docker" -w 4 -f
```

**Analyze Mode Features:**
- Web crawls baseline URL to discover all pages up to max depth
- Researches each discovered page in parallel
- Aggregates all research into comprehensive analysis document
- Creates agent-ready documentation with full context
- Output: `docs/{topic}_analyze.md`

**Arguments:**
- `-a, --analyze`: Enable analyze mode (with web crawling for URLs)
- `-p, --patterns`: Enable patterns mode
- `-b, --best-practices`: Enable best-practices mode
- `-t, --topic`: Topic or URL to research
- `-d, --max-depth`: Max crawl depth for URLs (default: 2)
- `-w, --workers`: Parallel workers (default: 1, max: 30)
- `-f, --force`: Overwrite existing files
- `-v, --verbose`: Enable debug output

This will automatically refresh all documentation with the latest research and best practices.

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Updated to reference project-current.md prompt
- v1.4 (2026-01-12 00:00:00): Added missing analyze type to research commands
- v1.5 (2026-01-12 00:00:00): Renamed PREFIXES variable to PROMPTS for clarity
- v1.6 (2026-01-12 00:00:00): Updated research script arguments from --prompt to --topics
- v1.7 (2026-01-12 00:00:00): Updated script path and arguments to match actual research.py interface
- v1.8 (2026-01-15 15:27:00): Updated for new research.py with comprehensive analyze mode and web crawling
