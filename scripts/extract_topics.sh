#!/bin/bash
# Extract topics from docs/ filenames and set TOPICS env var

topics=$(find docs -name "*.md" ! -name "*_analyze.md" -exec basename {} \; | grep "_" | cut -d'_' -f1 | sort -u | tr '\n' ' ')
export TOPICS="${topics% }"
echo "TOPICS=$TOPICS"
