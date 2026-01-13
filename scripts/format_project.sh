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
