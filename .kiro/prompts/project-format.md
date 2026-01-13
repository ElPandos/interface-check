---
title:        Project Format Instructions
inclusion:    always
version:      1.1
last-updated: 2026-01-12
status:       active
---

# Project Format Instructions

## Overview
Format all project files using language-specific best practices while respecting `.gitignore` exclusions.

## Python Files
```bash
# Format Python code with Ruff (primary)
uv run ruff format .

# Alternative: Black formatter
uv run black .

# Fix linting issues
uv run ruff check . --fix
```

## JavaScript/TypeScript Files
```bash
# Prettier for JS/TS files
npx prettier --write "**/*.{js,ts,jsx,tsx}"

# Alternative: Biome
npx @biomejs/biome format --write .
```

## JSON/YAML Files
```bash
# Format JSON files
find . -name "*.json" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" | xargs -I {} sh -c 'python -m json.tool {} > {}.tmp && mv {}.tmp {}'

# Format YAML with yq (if available)
find . -name "*.yml" -o -name "*.yaml" | grep -v -f .gitignore | xargs -I {} yq eval -i 'sort_keys(.)' {}
```

## Markdown Files
```bash
# Format markdown with prettier
npx prettier --write "**/*.md"

# Alternative: markdownlint
npx markdownlint-cli2 --fix "**/*.md"
```

## Shell Scripts
```bash
# Format shell scripts with shfmt
find . -name "*.sh" -not -path "./.git/*" | xargs shfmt -w -i 4
```

## Docker Files
```bash
# Format Dockerfile with hadolint (check only)
find . -name "Dockerfile*" -not -path "./.git/*" | xargs hadolint
```

## Complete Format Script
```bash
#!/bin/bash
set -e

echo "🔧 Formatting project files..."

# Python files (primary language)
echo "📝 Formatting Python files..."
uv run ruff format .
uv run ruff check . --fix

# JSON files
echo "📄 Formatting JSON files..."
find . -name "*.json" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./htmlcov/*" | while read -r file; do
    python -m json.tool "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

# Markdown files (if prettier available)
if command -v npx >/dev/null 2>&1; then
    echo "📖 Formatting Markdown files..."
    npx prettier --write "**/*.md" --ignore-path .gitignore
fi

# Shell scripts (if shfmt available)
if command -v shfmt >/dev/null 2>&1; then
    echo "🐚 Formatting shell scripts..."
    find . -name "*.sh" -not -path "./.git/*" | xargs shfmt -w -i 4
fi

echo "✅ Formatting complete!"
```

## Automated Formatting

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier
        types_or: [markdown, json, yaml]
```

### VS Code Settings
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Exclusions
Files automatically excluded via `.gitignore`:
- `.venv/`, `venv/`, `__pycache__/`
- `node_modules/`, `dist/`, `build/`
- `.git/`, `.mypy_cache/`, `.pytest_cache/`
- `htmlcov/`, `logs/`

## TODO.md Generation
```bash
# Generate TODO.md with current linting issues
echo "# TODO - Code Quality Issues

Generated on: $(date +%Y-%m-%d)

## Ruff Linting Issues" > TODO.md

# Append current ruff issues
uv run ruff check . >> TODO.md 2>/dev/null || echo "No ruff issues found" >> TODO.md

echo "
## Summary
- Run 'uv run ruff check .' to see current issues
- Priority: Focus on undefined names, blind exceptions, unused arguments

## Next Steps
1. Fix undefined imports
2. Replace blind Exception catches  
3. Remove unused arguments
4. Store async task references
5. Remove commented code" >> TODO.md
```

## Usage
```bash
# Quick format (Python only)
uv run ruff format .

# Complete project format
chmod +x format_project.sh
./format_project.sh

# Generate TODO list
echo "# TODO..." > TODO.md
```

## Version History

- v1.0 (2026-01-12): Initial version
- v1.1 (2026-01-12): Simplified TODO.md generation script
