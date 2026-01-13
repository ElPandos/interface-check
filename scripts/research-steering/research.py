#!/usr/bin/env python3
"""
Automated research and steering document generation using kiro-cli.

Usage examples:
    uv run scripts/research-steering/research.py -m patterns docker postgres redis
    uv run scripts/research-steering/research.py -m best-practices -t "ui threading concepts" -f -w 8
    uv run scripts/research-steering/research.py -m analyze -t "Research this web page: https://kiro.dev/docs/cli"
    uv run scripts/research-steering/research.py -m analyze kubernetes -s --verbose
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


def sanitize_filename(topic: str) -> str:
    """Convert topic to valid filename by removing/replacing invalid characters."""
    # Remove or replace invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', topic)  # Remove invalid chars
    sanitized = re.sub(r'https?://', '', sanitized)  # Remove protocol
    sanitized = re.sub(r'[.\s]+', '_', sanitized)    # Replace dots/spaces with underscore
    sanitized = re.sub(r'_+', '_', sanitized)        # Collapse multiple underscores
    sanitized = sanitized.strip('_')                 # Remove leading/trailing underscores
    
    # Limit length to avoid filesystem issues
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('_')
    
    return sanitized or "topic"  # Fallback if empty


def extract_existing_sources(content: str) -> set[str]:
    """Extract URLs from existing document's Sources & References section."""
    sources = set()
    
    # Look for Sources/References section
    patterns = [
        r"(?i)## Sources?\s*&?\s*References?\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)## References?\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)References:\s*\n(.*?)(?=\n##|\Z)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            refs_section = match.group(1)
            # Extract URLs from markdown links and plain URLs
            url_patterns = [
                r"\[.*?\]\((https?://[^\)]+)\)",  # [text](url)
                r"https?://[^\s\]]+",             # plain URLs
            ]
            for url_pattern in url_patterns:
                sources.update(re.findall(url_pattern, refs_section))
            break
    
    return sources


def extract_baseline_urls(topic: str) -> set[str]:
    """Extract baseline URLs from the topic string for deeper exploration."""
    baseline_urls = set()
    
    # Look for URLs in the topic
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, topic)
    
    for url in urls:
        # Clean up URL (remove trailing punctuation)
        url = re.sub(r'[.,;:!?]+$', '', url)
        baseline_urls.add(url)
    
    return baseline_urls


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


def build_prompt(topic: str, research_type: str, existing_sources: set[str] | None = None) -> str:
    """Generate kiro-cli prompt based on type and topic."""
    topic_human = topic.replace("-", " ").strip()

    templates = {
        "best-practices": f"Research best {topic_human} practices.",
        "patterns": f"Research common {topic_human} patterns and anti-patterns.",
        "analyze": f"Deep analysis of {topic_human} (strengths, weaknesses, trade-offs, current state).",
    }

    if research_type not in templates:
        raise ValueError(f"Unsupported research type: {research_type}")

    base_prompt = templates[research_type]
    
    # Add exclusion instruction for analyze mode with existing sources
    if research_type == "analyze" and existing_sources:
        # Extract baseline URLs from topic for deeper exploration
        baseline_urls = extract_baseline_urls(topic)
        
        if baseline_urls:
            base_prompt += f" Explore deeper into the baseline sites ({', '.join(baseline_urls)}) to find additional subpages, documentation sections, or related content."
        
        # Exclude already researched URLs
        excluded_urls = [url for url in existing_sources if url.startswith('http')]
        if excluded_urls:
            exclusion = f" Avoid these already researched URLs: {', '.join(excluded_urls[:5])}{'...' if len(excluded_urls) > 5 else ''}. Find NEW pages and sections from the same sites or related sources."
            base_prompt += exclusion

    # Use sanitized filename for steering document
    safe_topic = sanitize_filename(topic)
    steering_name = f"{safe_topic}_{research_type}.md"
    return f"{base_prompt} Use the research file to create/update .kiro/steering/{steering_name}"


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
        # Sanitize topic for filename
        safe_topic = sanitize_filename(topic)
        steering_path = project_root / STEERING_DIR / f"{safe_topic}_{research_type}.md"

        # Early skip check
        if skip_if_exists and steering_path.is_file():
            logger.info(f"{index}⏭ Skipped (already exists): {topic}")
            return topic, True, 0.0

        # Check for existing sources in analyze mode
        existing_sources = set()
        if research_type == "analyze" and steering_path.exists() and not force:
            existing_content = steering_path.read_text(encoding="utf-8")
            existing_sources = extract_existing_sources(existing_content)
            if existing_sources:
                logger.info(f"{index}📚 Found {len(existing_sources)} existing sources, will research new ones")

        prompt = build_prompt(topic, research_type, existing_sources if existing_sources else None)
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
        help="single topic as quoted string (alternative to positional args)",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=1,
        help="number of iterations to run (default: 1)",
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
        # Treat -t as a single topic, not space-separated
        topics.append(args.topics_str)

    if not topics:
        parser.error("No topics provided (use positional args or -t)")

    if args.force and args.skip:
        parser.error("Cannot combine --force and --skip")

    if not (1 <= args.workers <= MAX_WORKERS):
        parser.error(f"--workers must be between 1 and {MAX_WORKERS}")

    if args.iterations < 1:
        parser.error("--iterations must be at least 1")

    args.topics = topics
    return args


def has_new_sources_available(topic: str, research_type: str, project_root: Path) -> bool:
    """Check if there are potentially new sources to research."""
    if research_type != "analyze":
        return True  # Always research for non-analyze modes
    
    safe_topic = sanitize_filename(topic)
    steering_path = project_root / STEERING_DIR / f"{safe_topic}_{research_type}.md"
    
    if not steering_path.exists():
        return True  # No existing file, can research
    
    try:
        existing_content = steering_path.read_text(encoding="utf-8")
        existing_sources = extract_existing_sources(existing_content)
        baseline_urls = extract_baseline_urls(topic)
        
        # If we have baseline URLs but few sources, likely more to find
        if baseline_urls and len(existing_sources) < 10:
            return True
            
        # If no baseline URLs in topic, assume more sources available
        if not baseline_urls:
            return True
            
        return len(existing_sources) < 15  # Arbitrary threshold
    except Exception:
        return True  # On error, assume sources available


def run_single_iteration(
    topics: list[str],
    research_type: str,
    project_root: Path,
    logger: logging.Logger,
    iteration: int,
    total_iterations: int,
    **kwargs
) -> tuple[int, list[str], bool]:
    """Run a single iteration of research."""
    logger.info(f"=== Iteration {iteration}/{total_iterations} ===")
    
    # Check if any topics have potential new sources
    topics_with_sources = [
        topic for topic in topics 
        if has_new_sources_available(topic, research_type, project_root)
    ]
    
    if not topics_with_sources:
        logger.info("No topics have new sources available. Stopping iterations.")
        return 0, [], True  # success_count, failed, should_stop
    
    if len(topics_with_sources) < len(topics):
        skipped = len(topics) - len(topics_with_sources)
        logger.info(f"Skipping {skipped} topics with no new sources available")
    
    try:
        with ThreadPoolExecutor(max_workers=kwargs.get('workers', DEFAULT_WORKERS)) as pool:
            futures = [
                pool.submit(
                    run_research,
                    topic=topic,
                    research_type=research_type,
                    project_root=project_root,
                    logger=logger,
                    index=f"[{i:2d}/{len(topics_with_sources)}] ",
                    force=kwargs.get('force', False),
                    skip_if_exists=kwargs.get('skip_if_exists', False),
                )
                for i, topic in enumerate(topics_with_sources, 1)
            ]

            success_count = 0
            failed = []

            for future in as_completed(futures):
                try:
                    topic, ok, _ = future.result()
                    if ok:
                        success_count += 1
                    else:
                        failed.append(topic)
                except Exception as e:
                    logger.error(f"Future failed: {e}")
                    failed.append("unknown")

        total = len(topics_with_sources)
        success_rate = (success_count / total) * 100 if total > 0 else 0
        logger.info(f"Iteration {iteration} completed: {success_count}/{total} successful ({success_rate:.0f}%)")

        if failed:
            logger.warning(f"Failed topics in iteration {iteration}: {', '.join(failed)}")
            
        # Stop if all failed
        should_stop = success_count == 0 and len(failed) > 0
        return success_count, failed, should_stop
        
    except Exception as e:
        logger.error(f"Critical error in iteration {iteration}: {e}")
        return 0, [f"iteration-{iteration}"], True  # Stop on critical error


def main():
    args = parse_args()
    logger = setup_logging(args.verbose)

    try:
        root = find_project_root()
        logger.info(f"Project root: {root}")
        
        if args.iterations > 1:
            logger.info(f"Running {args.iterations} iterations")

        total_success = 0
        all_failed = []
        
        for iteration in range(1, args.iterations + 1):
            try:
                success_count, failed, should_stop = run_single_iteration(
                    topics=args.topics,
                    research_type=args.mode,
                    project_root=root,
                    logger=logger,
                    iteration=iteration,
                    total_iterations=args.iterations,
                    workers=args.workers,
                    force=args.force,
                    skip_if_exists=args.skip,
                )
                
                total_success += success_count
                all_failed.extend(failed)
                
                if should_stop:
                    logger.info(f"Stopping after iteration {iteration} due to no progress or critical error")
                    break
                    
                # Brief pause between iterations
                if iteration < args.iterations:
                    import time
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                logger.info(f"Interrupted during iteration {iteration}")
                raise
            except Exception as e:
                logger.error(f"Fatal error in iteration {iteration}: {e}")
                break

        # Final summary
        if args.iterations > 1:
            logger.info(f"=== Final Summary ===")
            logger.info(f"Total successful across all iterations: {total_success}")
            
        if all_failed:
            unique_failed = list(set(all_failed))
            logger.warning(f"Topics that failed: {', '.join(unique_failed)}")
            sys.exit(2)
            
        if total_success == 0:
            logger.error("No successful research completed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
