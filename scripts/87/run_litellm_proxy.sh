#!/bin/bash

echo "Killall liteLLM proxies"
killall litellm;
sleep 5;

echo "Start: Create liteLLM proxy on port: 4000 (lmstudio, ericai, openrouter ect.)"
uv run litellm --port 4000 --config ../../.config/litellm.yaml &
