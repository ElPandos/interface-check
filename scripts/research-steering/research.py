#!/usr/bin/env python3
"""
Automated research and steering document generation using kiro-cli.

Usage examples:
    uv run scripts/system/research-steering/research.py -m patterns docker postgres redis
    uv run scripts/system/research-steering/research.py -m best-practices -t "ui threading" -f -w 8
    uv run scripts/system/research-steering/research.py -m analyze kubernetes -s --verbose
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import os
from pathlib import Path
import re
import subprocess
import sys

from packaging import version  # pip install packaging (small & standard)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MAX_WORKERS = 30
DEFAULT_WORKERS = 1
TIMEOUT_SEC = 600  # 5 minutes
RESEARCH_TYPES = {"best-practices", "patterns", "analyze"}
STEERING_DIR = Path(".kiro") / "steering"
RESEARCH_BASE = Path(".kiro") / "research"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("research-steering")


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def extract_steering_content(kiro_output: str) -> str:
    """Extract the actual steering document content from kiro-cli output."""
    lines = kiro_output.split("\n")

    # Look for the start of the actual content (after research process)
    content_start = -1
    for i, line in enumerate(lines):
        # Find where the actual document content starts
        if line.strip().startswith("---") and "title:" in "\n".join(lines[i + 1 : i + 5]):
            content_start = i
            break
        elif line.strip().startswith("# ") and not any(
            x in line.lower() for x in ["research output", "complete response"]
        ):
            content_start = i
            break

    if content_start == -1:
        # Fallback: return everything after the last "Creating:" or "Updating:" line
        for i in reversed(range(len(lines))):
            if "Creating:" in lines[i] or "Updating:" in lines[i] or "Completed in" in lines[i]:
                content_start = i + 1
                break
        else:
            # Last resort: return the original content
            return kiro_output

    return "\n".join(lines[content_start:]).strip()


def find_project_root() -> Path:
    """Find nearest directory containing .kiro folder."""
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".kiro").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("No .kiro directory found in parent hierarchy")


def build_prompt(topic: str, research_type: str) -> str:
    """Generate kiro-cli prompt based on type and topic."""
    topic_human = topic.replace("-", " ").strip()

    templates = {
        "best-practices": f"Research best {topic_human} practices.",
        "patterns": f"Research common {topic_human} patterns and anti-patterns.",
        "analyze": f"Deep analysis of {topic_human} (strengths, weaknesses, trade-offs, current state).",
    }

    if research_type not in templates:
        raise ValueError(f"Unsupported research type: {research_type}")

    steering_name = f"{topic}_{research_type}.md"
    return f"{templates[research_type]} Use the research file to create/update .kiro/steering/{steering_name}"


def bump_version(content: str, today: str) -> tuple[str, str]:
    """Increment minor version and update frontmatter + version history."""
    # Find current version
    match = re.search(r"version:\s*(\d+\.\d+(?:\.\d+)?)", content)
    current = match.group(1) if match else "1.0"

    # Manual version bumping since packaging.version doesn't have bump_minor
    v = version.parse(current)
    new_version_str = f"{v.major}.{v.minor + 1}"

    # Update frontmatter
    content = re.sub(
        r"version:\s*[\d.]+",
        f"version:      {new_version_str}",
        content,
        count=1,
    )
    content = re.sub(
        r"last-updated:\s*\d{4}-\d{2}-\d{2}",
        f"last-updated: {today}",
        content,
        count=1,
    )

    # Add to version history
    history_pattern = r"(?s)## Version History\s*\n+(.*?)(?=\n##|\Z)"
    match = re.search(history_pattern, content)

    entry = f"- v{new_version_str} ({today}): Updated from latest research\n"

    if match:
        history = match.group(1).rstrip()
        new_history = history + "\n" + entry if history else entry
        content = re.sub(history_pattern, f"## Version History\n\n{new_history}", content)
    else:
        content = content.rstrip() + f"\n\n## Version History\n\n{entry}"

    return content, new_version_str


def update_or_create_steering(
    steering_path: Path,
    new_content: str,
    logger: logging.Logger,
    index: str,
    force: bool = False,
) -> bool:
    """Smart update or create steering file."""
    today = datetime.now().strftime("%Y-%m-%d")

    if not steering_path.exists() or force:
        steering_path.write_text(new_content, encoding="utf-8")
        action = "Created" if not steering_path.exists() else "Force overwritten"
        logger.info(f"{index}✓ {action}: {steering_path.name}")
        return True

    existing = steering_path.read_text(encoding="utf-8")

    # Skip if identical
    if existing.strip() == new_content.strip():
        logger.info(f"{index}⚪ No change needed: {steering_path.name}")
        return False

    updated, new_ver = bump_version(existing, today)
    steering_path.write_text(updated, encoding="utf-8")
    logger.info(f"{index}🔄 Updated to v{new_ver}: {steering_path.name}")
    return True


def run_research(
    topic: str,
    research_type: str,
    project_root: Path,
    logger: logging.Logger,
    index: str = "",
    force: bool = False,
    skip_if_exists: bool = False,
) -> tuple[str, bool, float]:
    """Run single research task."""
    start = datetime.now()

    try:
        steering_path = project_root / STEERING_DIR / f"{topic}_{research_type}.md"

        # Early skip check
        if skip_if_exists and steering_path.is_file():
            logger.info(f"{index}⏭ Skipped (already exists): {topic}")
            return topic, True, 0.0

        prompt = build_prompt(topic, research_type)
        cmd = ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", prompt]

        logger.info(f"{index}→ Researching {research_type}: {topic}")

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=TIMEOUT_SEC,
            env={**os.environ, "NO_COLOR": "1"},
        )

        duration = (datetime.now() - start).total_seconds()

        # Clean ANSI escape sequences from output
        clean_output = strip_ansi_codes(result.stdout.strip())

        if not clean_output:
            logger.warning(f"{index}⚠ No output received for {topic}")
            return topic, False, duration

        # Extract only the steering document content from kiro-cli output
        content = extract_steering_content(clean_output)

        updated = update_or_create_steering(steering_path, content, logger, index, force=force)

        logger.info(f"{index}✓ Done in {duration:.1f}s → {steering_path.name}")
        return topic, updated, duration

    except subprocess.TimeoutExpired:
        logger.error(f"{index}✗ Timeout ({TIMEOUT_SEC}s): {topic}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{index}✗ kiro-cli failed for {topic}: {e.returncode}")
        if e.stderr:
            logger.debug(f"stderr: {e.stderr.strip()}")
    except Exception as e:
        logger.exception(f"{index}✗ Unexpected error for {topic}: {e}")

    return topic, False, (datetime.now() - start).total_seconds()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate / update research steering documents via kiro-cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-m",
        "--mode",
        choices=RESEARCH_TYPES,
        required=True,
        help="research category",
    )
    parser.add_argument(
        "topics",
        nargs="*",
        help="topics to process (space-separated or quoted)",
    )
    parser.add_argument(
        "-t",
        "--topics-str",
        help="alternative: space-separated topics as single argument",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"concurrent workers (default {DEFAULT_WORKERS}, max {MAX_WORKERS})",
    )
    parser.add_argument("-f", "--force", action="store_true", help="overwrite existing files")
    parser.add_argument("-s", "--skip", action="store_true", help="skip if steering file exists")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")

    args = parser.parse_args()

    # Merge topic sources
    topics = args.topics or []
    if args.topics_str:
        topics.extend(args.topics_str.split())

    if not topics:
        parser.error("No topics provided (use positional args or -t)")

    if args.force and args.skip:
        parser.error("Cannot combine --force and --skip")

    if not (1 <= args.workers <= MAX_WORKERS):
        parser.error(f"--workers must be between 1 and {MAX_WORKERS}")

    args.topics = topics
    return args


def main():
    args = parse_args()
    logger = setup_logging(args.verbose)

    try:
        root = find_project_root()
        logger.info(f"Project root: {root}")

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [
                pool.submit(
                    run_research,
                    topic=topic,
                    research_type=args.mode,
                    project_root=root,
                    logger=logger,
                    index=f"[{i:2d}/{len(args.topics)}] ",
                    force=args.force,
                    skip_if_exists=args.skip,
                )
                for i, topic in enumerate(args.topics, 1)
            ]

            success_count = 0
            failed = []

            for future in as_completed(futures):
                topic, ok, _ = future.result()
                if ok:
                    success_count += 1
                else:
                    failed.append(topic)

        total = len(args.topics)
        logger.info(f"Completed: {success_count}/{total} successful ({(success_count / total) * 100:.0f}%)")

        if failed:
            logger.warning(f"Failed topics: {', '.join(failed)}")
            sys.exit(2)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
