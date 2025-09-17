#!/bin/bash

#echo "Killall ComfyUI processes"
#killall ./main.py;
#sleep 5;

echo "Start: Activate ComfyUI venv"
cd /home/emvekta/projects/ComfyUI
source .venv/bin/activate

echo "Start: Create ComfyUI on port: 8188"
uv run main.py &
