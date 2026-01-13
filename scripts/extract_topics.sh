#!/bin/bash
# Extract topics from steering document filenames and set TOPICS env var

topics=$(find .kiro/steering -name "*.md" -exec basename {} \; | grep "_" | cut -d'_' -f1 | sort -u | tr '\n' ' ')
export TOPICS="${topics% }"
echo "TOPICS=$TOPICS"
