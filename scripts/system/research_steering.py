#!/usr/bin/env python3
"""
Automated research and steering document generation script.
Usage: python sys_research_steering.py <topic1> <topic2> ...
"""

import argparse
import subprocess


def run_research(topic: str) -> None:
    """Run kiro-cli research for a specific topic."""
    prompt = f"Can you research {topic} best practices? and use the research file to create a .kiro/steering/{topic}-best-practices.md file"

    cmd = ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", prompt]

    print(f"Researching {topic}...")
    try:
        # Find project root (where .kiro directory exists)
        import os

        current_dir = os.getcwd()
        while not os.path.exists(os.path.join(current_dir, ".kiro")) and current_dir != "/":
            current_dir = os.path.dirname(current_dir)

        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=current_dir)
        print(f"✓ Completed research for {topic}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed research for {topic}: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Generate research and steering documents")
    parser.add_argument("topics", nargs="+", help="List of topics to research")

    args = parser.parse_args()

    print(f"Starting research for {len(args.topics)} topics...")

    for topic in args.topics:
        run_research(topic)

    print("All research completed!")


if __name__ == "__main__":
    main()
