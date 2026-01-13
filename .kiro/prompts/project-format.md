---
title:        Project Format Instructions
inclusion:    always
version:      1.5
last-updated: 2026-01-13
status:       active
---

# Project Format Instructions

## Quick Commands

```bash
# Primary (Python + auto-fix)
uv run ruff format . && uv run ruff check --fix .

# Complete project formatting
./scripts/format_project.sh
```

## Language-Specific Tools

### Python (Primary)
```bash
# Format + lint
uv run ruff format . && uv run ruff check --fix .

# CI check only
uv run ruff check --output-format=github .
```

### JSON
```bash
# Validate + format
find . -name "*.json" -not -path "./.git/*" -not -path "./.venv/*" -print0 | \
  xargs -0 -I {} sh -c 'python -m json.tool "$1" "$1.tmp" && mv "$1.tmp" "$1"' _ {}
```

### YAML
```bash
# With yamlfmt (preferred)
command -v yamlfmt >/dev/null && yamlfmt -w **/*.y*ml

# With yq (fallback)
find . -name "*.y*ml" -print0 | xargs -0 -I {} yq -i 'sort_keys(.)' {}
```

### Shell Scripts
```bash
# shfmt (2 spaces, simplify)
command -v shfmt >/dev/null && shfmt -w -i 2 -s **/*.sh
```

### Markdown
```bash
# mdformat (Ruff-aware)
uv run mdformat --check . || uv run mdformat .
```

## Complete Format Script

Create `scripts/format_project.sh`:
```bash
#!/bin/bash
set -e

echo "🔧 Formatting project files..."

# Python (primary)
uv run ruff format .
uv run ruff check . --fix

# JSON files
find . -name "*.json" -not -path "./.git/*" -not -path "./.venv/*" | while read -r file; do
    python -m json.tool "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

# Optional: Other formats
command -v shfmt >/dev/null && find . -name "*.sh" -not -path "./.git/*" | xargs shfmt -w -i 2
command -v yamlfmt >/dev/null && yamlfmt -w **/*.y*ml

echo "✅ Formatting complete!"
```

## Automation

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### VS Code Settings
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "[markdown]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
  "[json]": {"editor.defaultFormatter": "esbenp.prettier-vscode"}
}
```

## TODO Generation
```bash
# Generate TODO.md with current issues
{
  echo "# TODO - Code Quality Issues"
  echo "Generated: $(date +%Y-%m-%d)"
  echo
  echo "## Ruff Issues"
  uv run ruff check . 2>/dev/null || echo "No issues found"
} > TODO.md
```

## Version History

- v1.0 (2026-01-12): Initial version
- v1.1 (2026-01-12): Simplified TODO.md generation script
- v1.2 (2026-01-13): Optimized for brevity, removed redundant sections
- v1.3 (2026-01-13): Fixed formatting inconsistencies
- v1.4 (2026-01-13): Streamlined structure, removed excessive whitespace, consistent formatting
- v1.5 (2026-01-13): Fixed JSON command shell escaping, updated pre-commit version
