#!/bin/bash
set -e

echo "🔧 Formatting project files..."

# Python (parallel)
uv run ruff format . &
uv run ruff check . --fix &
wait

# JSON files (parallel with error handling)
if command -v jq >/dev/null; then
    find . -name "*.json" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./.logs/*" -print0 | \
        xargs -0 -P 4 -I {} sh -c 'jq --indent 2 . "{}" > "{}.tmp" 2>/dev/null && mv "{}.tmp" "{}" || rm -f "{}.tmp"'
else
    find . -name "*.json" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./.logs/*" -print0 | \
        xargs -0 -P 4 -I {} sh -c 'python -m json.tool "{}" > "{}.tmp" 2>/dev/null && mv "{}.tmp" "{}" || rm -f "{}.tmp"'
fi

# Shell scripts (if shfmt available)
command -v shfmt >/dev/null && find . -name "*.sh" -not -path "./.git/*" -print0 | xargs -0 shfmt -w -i 2

echo "✅ Formatting complete!"
