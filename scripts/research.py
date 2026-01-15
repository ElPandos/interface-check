#!/usr/bin/env python3
"""
Automated research and documentation generation using kiro-cli.

This script generates standardized documentation (docs/*.md) by invoking kiro-cli
with structured prompts. It supports three research modes and handles parallel
execution, version bumping, and comprehensive web crawling for analyze mode.

Modes:
    patterns (-p)       : Research common patterns and anti-patterns
    best-practices (-b) : Research current best practices for 2025-2026
    analyze (-a)        : Deep analysis with web crawling and comprehensive research
                         - Crawls baseline URL to discover all pages up to max_depth
                         - Researches each discovered page in parallel
                         - Aggregates all research into comprehensive analysis document
                         - Creates agent-ready documentation with full context

Features:
    - Parallel execution with configurable workers (max 30)
    - Automatic version bumping for existing files
    - Web crawling for analyze mode (discovers all endpoints at each depth level)
    - Comprehensive research aggregation (all pages researched and synthesized)
    - Live execution timer with progress display
    - Structured logging to console and file (.logs/)
    - Skip/force options for existing files
    - 10-minute timeout per research task

Analyze Mode Details:
    When -a flag is used with a URL:
    1. Crawls the baseline URL to discover all linked pages
    2. Organizes discovered pages by depth level (0 to max_depth)
    3. Researches each discovered page in parallel using kiro-cli
    4. Aggregates all research into a single comprehensive document
    5. Creates agent-ready documentation that fully explains the technology

    The resulting _analyze.md file includes:
    - Overview synthesizing all researched pages
    - Core concepts and architecture
    - Key features and capabilities from all pages
    - Usage patterns and best practices
    - Configuration and setup details
    - API and integration information
    - Common pitfalls and anti-patterns
    - Advanced topics
    - Complete endpoint reference organized by depth
    - All source URLs researched

Output Format:
    All generated files follow the documentation standard:
    - YAML frontmatter (title, inclusion, version, last-updated, status)
    - Core Principles, Essential Patterns/Practices, Anti-Patterns
    - Implementation Guidelines, Success Metrics, Sources & References
    - Version History

Usage:
    uv run scripts/research.py -p docker redis              # patterns for multiple topics
    uv run scripts/research.py -b -p kubernetes             # both modes for one topic
    uv run scripts/research.py -a -t "https://example.com/docs"  # comprehensive analyze with crawling
    uv run scripts/research.py -a -t "https://example.com/docs" -d 3 -w 4  # depth 3, 4 workers
    uv run scripts/research.py -a -b -p docker -w 4 -f      # all modes, 4 workers, force

Arguments:
    topics              : Topics to research (positional)
    -t, --topic         : Single topic (use for URLs or topics with spaces)
    -a, --analyze       : Enable analyze mode (with web crawling for URLs)
    -p, --patterns      : Enable patterns mode
    -b, --best-practices: Enable best-practices mode
    -w, --workers       : Parallel workers (default: 1, max: 30)
    -n, --iterations    : Iterations for non-URL analyze mode (default: 1, ignored for URLs)
    -d, --max-depth     : Max crawl depth for analyze mode URLs (default: 2)
    -f, --force         : Overwrite existing files
    -s, --skip          : Skip if file exists
    -v, --verbose       : Enable debug output

Exit Codes:
    0 : All research completed successfully
    1 : No research completed
    2 : Some research failed
    130: Interrupted by user (Ctrl+C)
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from packaging import version
import requests

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MAX_WORKERS = 30
DEFAULT_WORKERS = 1
DEFAULT_ITERATIONS = 1
DEFAULT_MAX_DEPTH = 2
TIMEOUT_SEC = 600


# Terminal colors
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


# Icons (all double-width for consistent alignment)
class Icons:
    ROCKET = "🚀"
    CHECK = "✅"
    CROSS = "❌"
    ARROW = "➡️"
    SKIP = "⏭️"
    WARN = "🔶"
    PIN = "📍"
    GEAR = "🔧"
    CLOCK = "🕐"
    SPARKLE = "✨"
    FOLDER = "📁"
    SEARCH = "🔍"
    HOURGLASS = "⏳"


# Mode colors (consistent across all displays)
MODE_COLORS = {"analyze": C.MAGENTA, "patterns": C.BLUE, "best-practices": C.GREEN}


# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────


class ExecutionTimer:
    """Live execution timer that counts up."""

    def __init__(self, prefix: str = "", mode: str = ""):
        self._prefix = prefix
        self._mode = mode
        self._color = MODE_COLORS.get(mode, C.WHITE)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._start_time: float = 0

    def start(self) -> None:
        """Start the timer display."""
        self._start_time = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        """Stop the timer and return elapsed time."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        elapsed = time.time() - self._start_time
        # Clear the timer line
        print(f"\r{' ' * 80}\r", end="", flush=True)
        return elapsed

    def _run(self) -> None:
        """Timer thread loop."""
        while not self._stop_event.is_set():
            elapsed = time.time() - self._start_time
            mins, secs = divmod(int(elapsed), 60)
            timer_str = f"{mins:02d}:{secs:02d}"
            print(
                f"\r{self._prefix}{Icons.HOURGLASS} {self._color}Executing...{C.RESET} {C.DIM}{timer_str}{C.RESET}",
                end="",
                flush=True,
            )
            self._stop_event.wait(1)


class StylishFormatter(logging.Formatter):
    """Custom formatter with colors and icons."""

    FORMATS = {
        logging.DEBUG: f"{C.DIM}%(asctime)s │ DEBUG   │ %(message)s{C.RESET}",
        logging.INFO: f"{C.CYAN}%(asctime)s{C.RESET} │ {C.GREEN}INFO{C.RESET}    │ %(message)s",
        logging.WARNING: f"{C.CYAN}%(asctime)s{C.RESET} │ {C.YELLOW}WARNING{C.RESET} │ {C.YELLOW}%(message)s{C.RESET}",
        logging.ERROR: f"{C.CYAN}%(asctime)s{C.RESET} │ {C.RED}ERROR{C.RESET}   │ {C.RED}%(message)s{C.RESET}",
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logging(verbose: bool = False, project_root: Path | None = None) -> logging.Logger:
    """Configure logging with stylish console output and file logging."""
    logger = logging.getLogger("research")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Only add console handler if not already present
    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(StylishFormatter())
        logger.addHandler(console)

    # Add file handler if project_root provided
    if project_root:
        log_dir = project_root / ".logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"research_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s │ %(levelname)-7s │ %(message)s", datefmt="%H:%M:%S"))
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.debug(f"Logging to: {log_file}")

    return logger


def print_banner(modes: list[str], topics: list[str], workers: int, iterations: int = 1) -> None:
    """Print startup banner."""
    modes_str = ", ".join(modes)
    topics_str = f"{len(topics)} topic(s)"

    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════════╗{C.RESET}")
    print(
        f"{C.BOLD}{C.CYAN}║{C.RESET}  {Icons.ROCKET} {C.BOLD}Research Steering Generator{C.RESET}                              {C.CYAN}║{C.RESET}"
    )
    print(f"{C.BOLD}{C.CYAN}╠══════════════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {Icons.GEAR} Modes:      {C.YELLOW}{modes_str:<45}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {Icons.FOLDER} Topics:     {C.WHITE}{topics_str:<45}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {Icons.SPARKLE} Workers:    {C.WHITE}{workers:<45}{C.RESET}{C.CYAN}║{C.RESET}")
    if iterations > 1:
        print(f"{C.CYAN}║{C.RESET}  {Icons.CLOCK} Iterations: {C.WHITE}{iterations:<45}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════════╝{C.RESET}\n")


def print_mode_header(mode: str) -> None:
    """Print mode section header."""
    color = MODE_COLORS.get(mode, C.WHITE)
    print(f"\n{color}{'─' * 60}")
    print(f"{C.BOLD}  {Icons.SEARCH} Mode: {mode.upper()}")
    print(f"{'─' * 60}{C.RESET}\n")


def print_summary(total_success: int, total_failed: int, duration: float) -> None:
    """Print final summary."""
    status_color = C.GREEN if total_failed == 0 else C.YELLOW if total_success > 0 else C.RED
    status_icon = Icons.CHECK if total_failed == 0 else Icons.WARN if total_success > 0 else Icons.CROSS
    status_text = "SUCCESS" if total_failed == 0 else "PARTIAL" if total_success > 0 else "FAILED"

    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════════╗{C.RESET}")
    print(
        f"{C.CYAN}║{C.RESET}  {Icons.SPARKLE} {C.BOLD}Summary{C.RESET}                                                  {C.CYAN}║{C.RESET}"
    )
    print(f"{C.CYAN}╠══════════════════════════════════════════════════════════════╣{C.RESET}")
    print(
        f"{C.CYAN}║{C.RESET}  {status_icon} Status:    {status_color}{C.BOLD}{status_text:<46}{C.RESET}{C.CYAN}║{C.RESET}"
    )
    print(f"{C.CYAN}║{C.RESET}  {Icons.CHECK} Completed: {C.GREEN}{total_success:<46}{C.RESET}{C.CYAN}║{C.RESET}")
    print(
        f"{C.CYAN}║{C.RESET}  {Icons.CROSS} Failed:    {C.RED if total_failed > 0 else C.DIM}{total_failed:<46}{C.RESET}{C.CYAN}║{C.RESET}"
    )
    print(f"{C.CYAN}║{C.RESET}  {Icons.CLOCK} Duration:  {C.WHITE}{f'{duration:.1f}s':<46}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════════╝{C.RESET}")


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────


def sanitize_filename(topic: str) -> str:
    """Convert topic to valid filename."""
    s = re.sub(r'[<>:"/\\|?*]', "", topic)
    s = re.sub(r"https?://", "", s)
    s = re.sub(r"[.\s]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:100].rstrip("_") if len(s) > 100 else s or "topic"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences."""
    return re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])").sub("", text)


def find_project_root() -> Path:
    """Find nearest directory containing .kiro folder."""
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".kiro").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("No .kiro directory found in parent hierarchy")


def extract_baseline_urls(topic: str) -> set[str]:
    """Extract URLs from topic string."""
    urls = re.findall(r"https?://[^\s]+", topic)
    return {re.sub(r"[.,;:!?]+$", "", url) for url in urls}


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint Tracking (for analyze mode)
# ──────────────────────────────────────────────────────────────────────────────


def get_tracking_path(project_root: Path, topic: str) -> Path:
    """Get endpoint tracking file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    tracking_dir = project_root / ".kiro" / "research" / today / "analyze" / "endpoints"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    return tracking_dir / f"{sanitize_filename(topic)}_endpoints.json"


def load_endpoints(project_root: Path, topic: str) -> set[str]:
    """Load previously discovered endpoints."""
    path = get_tracking_path(project_root, topic)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text())
        endpoints = set()
        for v in data.values():
            if isinstance(v, dict) and "endpoints" in v:
                endpoints.update(v["endpoints"])
        return endpoints
    except Exception:
        return set()


def save_endpoints(project_root: Path, topic: str, iteration: int, endpoints: set[str]) -> None:
    """Save newly discovered endpoints."""
    path = get_tracking_path(project_root, topic)
    existing = load_endpoints(project_root, topic)
    new_endpoints = endpoints - existing

    if not new_endpoints:
        return

    data = json.loads(path.read_text()) if path.exists() else {}
    data[f"iteration_{iteration}"] = {"timestamp": datetime.now().isoformat(), "endpoints": sorted(new_endpoints)}
    path.write_text(json.dumps(data, indent=2))


def extract_endpoints(content: str, baseline_url: str, max_depth: int = 3) -> set[str]:
    """Extract relative endpoints from content."""
    parsed = urlparse(baseline_url)
    base_path = parsed.path.rstrip("/")

    urls = re.findall(r"https?://[^\s\]<>\"'(),]+", content)
    endpoints = set()

    for url in urls:
        url = url.rstrip(".,;:!?")
        try:
            p = urlparse(url)
            if p.netloc == parsed.netloc:
                path = p.path.rstrip("/")
                if path.startswith(base_path) and path != base_path:
                    rel = path[len(base_path) :] if base_path else path
                    if rel and len(rel) > 1:
                        depth = len([s for s in rel.split("/") if s])
                        if depth <= max_depth:
                            endpoints.add(rel)
        except Exception:
            continue

    return endpoints


def crawl_url(url: str, logger: logging.Logger) -> set[str]:
    """Fetch URL and extract all links."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(url, href)
            # Remove fragments and query params
            parsed = urlparse(full_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            links.add(clean_url)

        return links
    except Exception as e:
        logger.debug(f"Failed to crawl {url}: {e}")
        return set()


def discover_endpoints(baseline_url: str, max_depth: int, logger: logging.Logger) -> dict[int, set[str]]:
    """Crawl website to discover all endpoints up to max_depth."""
    parsed = urlparse(baseline_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    base_path = parsed.path.rstrip("/")

    # Track URLs by depth level
    endpoints_by_depth: dict[int, set[str]] = {0: {baseline_url}}
    visited = {baseline_url}

    logger.info(f"{Icons.SEARCH} Crawling {baseline_url} (max depth: {max_depth})")

    for depth in range(max_depth):
        current_level = endpoints_by_depth[depth]
        next_level = set()

        logger.info(f"  Depth {depth}: {len(current_level)} URLs to crawl")

        for url in current_level:
            links = crawl_url(url, logger)

            for link in links:
                # Only include links from same domain and under base path
                if link.startswith(baseline_url) and link not in visited:
                    # Calculate depth
                    link_path = urlparse(link).path.rstrip("/")
                    rel_path = link_path.removeprefix(base_path)
                    link_depth = len([s for s in rel_path.split("/") if s])

                    if link_depth == depth + 1:
                        next_level.add(link)
                        visited.add(link)

        if next_level:
            endpoints_by_depth[depth + 1] = next_level
            logger.info(f"  Depth {depth + 1}: Found {len(next_level)} new URLs")
        else:
            break

    total = sum(len(urls) for urls in endpoints_by_depth.values())
    logger.info(f"{Icons.CHECK} Discovered {total} total URLs across {len(endpoints_by_depth)} depth levels")

    return endpoints_by_depth


# ──────────────────────────────────────────────────────────────────────────────
# File Operations
# ──────────────────────────────────────────────────────────────────────────────


def get_steering_path(project_root: Path, topic: str, research_type: str) -> Path:
    """Get steering file path."""
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir / f"{sanitize_filename(topic)}_{research_type}.md"


def extract_content(kiro_output: str, logger: logging.Logger | None = None) -> str | None:
    """Extract steering document from kiro-cli output. Returns None if only summary found."""
    lines = kiro_output.split("\n")

    # Look for YAML frontmatter first (most reliable)
    for i, line in enumerate(lines):
        if line.strip() == "---" and i + 4 < len(lines):
            next_lines = "\n".join(lines[i + 1 : i + 5])
            if "title:" in next_lines:
                content = "\n".join(lines[i:]).strip()
                # Verify it's proper steering format
                if "inclusion:" in content and "version:" in content:
                    return content

    # Look for markdown heading (but not research output)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and "research output" not in stripped.lower():
            return "\n".join(lines[i:]).strip()

    # Detect kiro-cli summary responses (no actual content found)
    first_line = lines[0].strip() if lines else ""
    if first_line.startswith(("Here's what I found", "[1.")):
        if logger:
            logger.debug(f"Detected summary response, first line: {first_line[:80]}")
    elif logger:
        logger.debug(f"No valid content found. First 200 chars: {kiro_output[:200]}")

    return None


def bump_version(content: str, today: str) -> tuple[str, str]:
    """Increment version and update frontmatter."""
    match = re.search(r"version:\s*(\d+\.\d+)", content)
    current = match.group(1) if match else "1.0"
    v = version.parse(current)
    new_ver = f"{v.major}.{v.minor + 1}"

    content = re.sub(r"version:\s*[\d.]+", f"version:      {new_ver}", content, count=1)
    content = re.sub(r"last-updated:\s*\d{4}-\d{2}-\d{2}", f"last-updated: {today}", content, count=1)

    entry = f"- v{new_ver} ({today}): Updated from latest research\n"
    match = re.search(r"(?s)## Version History\s*\n+(.*?)(?=\n##|\Z)", content)
    if match:
        history = match.group(1).rstrip() + "\n" + entry
        content = re.sub(r"(?s)## Version History\s*\n+.*?(?=\n##|\Z)", f"## Version History\n\n{history}", content)
    else:
        content = content.rstrip() + f"\n\n## Version History\n\n{entry}"

    return content, new_ver


# ──────────────────────────────────────────────────────────────────────────────
# Prompt Building
# ──────────────────────────────────────────────────────────────────────────────


def build_prompt(topic: str, research_type: str, excluded_urls: set[str] | None = None, url_context: str = "") -> str:
    """Generate kiro-cli prompt."""
    topic_human = topic.replace("-", " ").strip()
    title = topic_human.title()
    today = datetime.now().strftime("%Y-%m-%d")

    section_name = {"best-practices": "Practices", "patterns": "Patterns", "analyze": "Findings"}[research_type]
    type_title = {"best-practices": "Best Practices", "patterns": "Patterns", "analyze": "Analysis"}[research_type]

    templates = {
        "best-practices": f"Research current {topic_human} best practices for 2025-2026.",
        "patterns": f"Research common {topic_human} patterns and anti-patterns.",
        "analyze": f"Deep analysis of {topic_human}. {url_context}",
    }

    prompt = templates[research_type]

    if research_type == "analyze" and excluded_urls:
        urls = [u for u in excluded_urls if u.startswith("http")][:5]
        if urls:
            prompt += f" Avoid already researched: {', '.join(urls)}. Find NEW content."

    prompt += f"""

OUTPUT FORMAT - Create this EXACT structure:

---
title:        {title} {type_title}
inclusion:    always
version:      1.0
last-updated: {today}
status:       active
---

# {title} {type_title}

## Core Principles
[3-5 key principles]

## Essential {section_name}
[Detailed practical guidance]

## Anti-Patterns to Avoid
[Common mistakes]

## Implementation Guidelines
[Step-by-step guidance]

## Success Metrics
[How to measure]

## Sources & References
[URLs researched]

## Version History
- v1.0 ({today}): Initial version

CRITICAL: Output COMPLETE document, not summary. Save to docs/{sanitize_filename(topic)}_{research_type}.md"""

    return prompt


# ──────────────────────────────────────────────────────────────────────────────
# Research Execution
# ──────────────────────────────────────────────────────────────────────────────


def research_url(
    url: str,
    project_root: Path,
    logger: logging.Logger,
    index: str = "",
) -> tuple[str, str, bool]:
    """Research a single URL and return its content."""
    try:
        prompt = f"Research and summarize key information from: {url}\n\nProvide comprehensive analysis covering: purpose, key features, technical details, usage patterns, and important considerations."

        logger.info(f"{index}{Icons.ARROW} Researching: {url[:60]}")

        timer = ExecutionTimer(prefix=f"{index}", mode="analyze")
        timer.start()

        try:
            result = subprocess.run(
                ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", prompt],
                check=True,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=TIMEOUT_SEC,
                env={**os.environ, "NO_COLOR": "1"},
            )
        finally:
            duration = timer.stop()

        content = strip_ansi(result.stdout.strip())
        logger.info(f"{index}{Icons.CHECK} Done in {duration:.1f}s")
        return url, content, True

    except Exception as e:
        logger.error(f"{index}{Icons.CROSS} Failed: {e}")
        return url, "", False


def run_analyze_comprehensive(
    baseline_url: str,
    project_root: Path,
    logger: logging.Logger,
    workers: int,
    max_depth: int,
    force: bool,
) -> tuple[bool, float]:
    """Comprehensive analyze mode: crawl and research all discovered endpoints."""
    start = datetime.now()

    # Discover all endpoints
    endpoints_by_depth = discover_endpoints(baseline_url, max_depth, logger)
    all_urls = []
    for depth in sorted(endpoints_by_depth.keys()):
        all_urls.extend(sorted(endpoints_by_depth[depth]))

    if not all_urls:
        logger.error("No URLs discovered")
        return False, 0.0

    logger.info(f"\n{Icons.SPARKLE} Researching {len(all_urls)} discovered URLs with {workers} workers\n")

    # Research all URLs in parallel
    url_research: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(research_url, url, project_root, logger, f"[{i}/{len(all_urls)}] ")
            for i, url in enumerate(all_urls, 1)
        ]

        for future in as_completed(futures):
            url, content, ok = future.result()
            if ok and content:
                url_research[url] = content

    logger.info(f"\n{Icons.CHECK} Completed research for {len(url_research)}/{len(all_urls)} URLs")

    # Aggregate all research into comprehensive document
    logger.info(f"{Icons.SPARKLE} Generating comprehensive analysis document...")

    parsed = urlparse(baseline_url)
    topic = f"{parsed.netloc}{parsed.path}".replace("/", "_").replace(".", "_")

    # Build comprehensive prompt with all research
    aggregated_research = "\n\n".join([f"## Research from {url}\n\n{content}" for url, content in url_research.items()])

    comprehensive_prompt = f"""Based on comprehensive research of {baseline_url} and {len(url_research)} related pages, create a detailed analysis document.

RESEARCHED CONTENT:
{aggregated_research}

Create a comprehensive analysis document that synthesizes ALL the researched information into a cohesive guide. This document will be used by AI agents to fully understand how this technology/service works.

OUTPUT FORMAT - Create this EXACT structure:

---
title:        {parsed.netloc.title()} Comprehensive Analysis
inclusion:    always
version:      1.0
last-updated: {datetime.now().strftime("%Y-%m-%d")}
status:       active
---

# {parsed.netloc.title()} Comprehensive Analysis

## Overview
[Comprehensive overview synthesizing all researched pages]

## Core Concepts
[Key concepts and principles discovered across all pages]

## Architecture & Components
[System architecture, components, and how they interact]

## Key Features & Capabilities
[Detailed feature breakdown from all researched pages]

## Usage Patterns & Best Practices
[How to use effectively, patterns discovered]

## Configuration & Setup
[Setup instructions, configuration options]

## API & Integration
[API details, integration patterns if applicable]

## Common Pitfalls & Anti-Patterns
[Issues to avoid based on research]

## Advanced Topics
[Advanced features and use cases]

## Endpoint Reference
[List of all {len(all_urls)} researched URLs organized by depth]
{chr(10).join([f"- Depth {depth}: {len(urls)} pages" for depth, urls in endpoints_by_depth.items()])}

## Sources & References
[All {len(url_research)} URLs researched]

## Version History
- v1.0 ({datetime.now().strftime("%Y-%m-%d")}): Initial comprehensive analysis from {len(url_research)} pages

CRITICAL: This document must be comprehensive enough for an AI agent to fully understand the technology. Include ALL important details from the research."""

    timer = ExecutionTimer(prefix="", mode="analyze")
    timer.start()

    try:
        result = subprocess.run(
            ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", comprehensive_prompt],
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=TIMEOUT_SEC * 2,  # Double timeout for comprehensive doc
            env={**os.environ, "NO_COLOR": "1"},
        )
    finally:
        duration = timer.stop()

    # Save the comprehensive document
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    output_path = docs_dir / f"{sanitize_filename(topic)}_analyze.md"

    content = strip_ansi(result.stdout.strip())
    output_path.write_text(content)

    total_duration = (datetime.now() - start).total_seconds()
    logger.info(f"\n{Icons.CHECK} {C.GREEN}Created comprehensive analysis{C.RESET} {Icons.ARROW} {output_path}")
    logger.info(f"{Icons.CLOCK} Total time: {total_duration:.1f}s")

    return True, total_duration


def run_research(
    topic: str,
    research_type: str,
    project_root: Path,
    logger: logging.Logger,
    index: str = "",
    force: bool = False,
    skip_if_exists: bool = False,
    iteration: int = 1,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> tuple[str, bool, float]:
    """Execute single research task."""
    start = datetime.now()
    steering_path = get_steering_path(project_root, topic, research_type)

    try:
        if skip_if_exists and steering_path.exists():
            logger.info(f"{index}{Icons.SKIP} {C.DIM}Skipped (exists): {topic[:40]}{C.RESET}")
            return topic, True, 0.0

        # Build exclusions for analyze mode
        excluded = set()
        if research_type == "analyze":
            baseline_urls = extract_baseline_urls(topic)
            endpoints = load_endpoints(project_root, topic)
            if baseline_urls and endpoints:
                base = list(baseline_urls)[0]
                excluded = {f"{base.rstrip('/')}{ep}" for ep in endpoints}

        prompt = build_prompt(topic, research_type, excluded or None)

        iter_info = f" (iter {iteration})" if iteration > 1 else ""
        logger.info(
            f"{index}{Icons.ARROW} {C.BOLD}Researching{C.RESET} {C.YELLOW}{research_type}{C.RESET}{iter_info}: {C.WHITE}{topic[:50]}{C.RESET}"
        )

        # Start execution timer
        timer = ExecutionTimer(prefix=f"{index}", mode=research_type)
        timer.start()

        try:
            result = subprocess.run(
                ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", prompt],
                check=True,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=TIMEOUT_SEC,
                env={**os.environ, "NO_COLOR": "1"},
            )
        finally:
            duration = timer.stop()

        # Check if kiro-cli created/updated the file directly
        if steering_path.exists():
            file_content = steering_path.read_text()
            file_mtime = steering_path.stat().st_mtime
            # File was modified during this run (within last duration + buffer)
            if file_mtime > start.timestamp() - 5:
                # Verify it has valid steering format
                if "---" in file_content and "title:" in file_content:
                    logger.info(f"{index}{Icons.CHECK} {C.GREEN}Created{C.RESET} {Icons.ARROW} {steering_path}")
                    logger.info(f"{index}{Icons.CLOCK} {C.DIM}Done in {duration:.1f}s{C.RESET}")
                    return topic, True, duration

        # Fallback: try to extract content from stdout
        content = extract_content(strip_ansi(result.stdout.strip()), logger)

        if not content:
            logger.warning(f"{index}{Icons.WARN} No valid steering content (got summary response)")
            return topic, False, duration

        # Track endpoints for analyze mode
        if research_type == "analyze":
            baseline_urls = extract_baseline_urls(topic)
            if baseline_urls:
                new_eps = extract_endpoints(content, list(baseline_urls)[0], max_depth)
                save_endpoints(project_root, topic, iteration, new_eps)
                logger.info(f"{index}{Icons.PIN} {C.DIM}Found {len(new_eps)} endpoints (depth {max_depth}){C.RESET}")

        # Write file
        today = datetime.now().strftime("%Y-%m-%d")
        if steering_path.exists() and not force:
            existing = steering_path.read_text()
            if existing.strip() != content.strip():
                content, new_ver = bump_version(existing, today)
                steering_path.write_text(content)
                logger.info(f"{index}{Icons.CHECK} {C.GREEN}Updated v{new_ver}{C.RESET} {Icons.ARROW} {steering_path}")
            else:
                logger.info(f"{index}{Icons.CHECK} {C.DIM}No changes{C.RESET}: {steering_path}")
        else:
            action = "Overwrote" if steering_path.exists() else "Created"
            steering_path.write_text(content)
            logger.info(f"{index}{Icons.CHECK} {C.GREEN}{action}{C.RESET} {Icons.ARROW} {steering_path}")

        logger.info(f"{index}{Icons.CLOCK} {C.DIM}Done in {duration:.1f}s{C.RESET}")
        return topic, True, duration

    except subprocess.TimeoutExpired:
        logger.error(f"{index}{Icons.CROSS} Timeout ({TIMEOUT_SEC}s): {topic}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{index}{Icons.CROSS} kiro-cli failed: {e.returncode}")
    except Exception as e:
        logger.exception(f"{index}{Icons.CROSS} Error: {e}")

    return topic, False, (datetime.now() - start).total_seconds()


def run_mode(
    mode: str,
    topics: list[str],
    project_root: Path,
    logger: logging.Logger,
    workers: int,
    force: bool,
    skip: bool,
    iterations: int = 1,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> tuple[int, list[str]]:
    """Run research for all topics in a mode."""
    print_mode_header(mode)

    total_success, all_failed = 0, []

    # Special handling for analyze mode with URLs
    if mode == "analyze":
        for topic in topics:
            if topic.startswith("http://") or topic.startswith("https://"):
                # Comprehensive crawl and research
                ok, _ = run_analyze_comprehensive(
                    baseline_url=topic,
                    project_root=project_root,
                    logger=logger,
                    workers=workers,
                    max_depth=max_depth,
                    force=force,
                )
                if ok:
                    total_success += 1
                else:
                    all_failed.append(topic)
            else:
                # Non-URL topics use standard research
                for iteration in range(1, iterations + 1):
                    topic_result, ok, _ = run_research(
                        topic=topic,
                        research_type=mode,
                        project_root=project_root,
                        logger=logger,
                        index="[1/1] ",
                        force=force,
                        skip_if_exists=skip,
                        iteration=iteration,
                        max_depth=max_depth,
                    )
                    if ok:
                        total_success += 1
                    else:
                        all_failed.append(topic)
    else:
        # Standard mode for patterns and best-practices
        for iteration in range(1, iterations + 1):
            if iterations > 1:
                logger.info(f"\n{Icons.ARROW} {C.BOLD}Iteration {iteration}/{iterations}{C.RESET}")

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [
                    pool.submit(
                        run_research,
                        topic=topic,
                        research_type=mode,
                        project_root=project_root,
                        logger=logger,
                        index=f"[{i}/{len(topics)}] ",
                        force=force,
                        skip_if_exists=skip,
                        iteration=iteration,
                        max_depth=max_depth,
                    )
                    for i, topic in enumerate(topics, 1)
                ]

                for future in as_completed(futures):
                    topic, ok, _ = future.result()
                    if ok:
                        total_success += 1
                    else:
                        all_failed.append(topic)

    rate = (total_success / len(topics)) * 100 if topics else 0
    logger.info(f"{Icons.SPARKLE} {C.BOLD}Mode complete:{C.RESET} {total_success}/{len(topics)} ({rate:.0f}%)")

    return total_success, all_failed


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate documentation via kiro-cli research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -p docker redis                          # patterns for multiple topics
  %(prog)s -b -p kubernetes                         # both modes for one topic
  %(prog)s -a -t "https://docs.example.com"         # comprehensive analyze with web crawling
  %(prog)s -a -t "https://docs.example.com" -d 3 -w 4  # depth 3, 4 parallel workers
  %(prog)s -a -b -p docker -w 4 -f                  # all modes, 4 workers, force
""",
    )

    parser.add_argument("-a", "--analyze", action="store_true", help="analyze mode (with web crawling for URLs)")
    parser.add_argument("-p", "--patterns", action="store_true", help="patterns mode")
    parser.add_argument("-b", "--best-practices", action="store_true", help="best-practices mode")
    parser.add_argument("topics", nargs="*", help="topics to research")
    parser.add_argument("-t", "--topic", help="single topic (for URLs or spaces)")
    parser.add_argument(
        "-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"parallel workers (default: {DEFAULT_WORKERS})"
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"iterations for non-URL analyze mode (default: {DEFAULT_ITERATIONS}, ignored for URLs)",
    )
    parser.add_argument(
        "-d",
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help=f"max crawl depth for analyze mode URLs (default: {DEFAULT_MAX_DEPTH})",
    )
    parser.add_argument("-f", "--force", action="store_true", help="overwrite existing")
    parser.add_argument("-s", "--skip", action="store_true", help="skip if exists")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug output")

    args = parser.parse_args()

    # Collect topics
    topics = args.topics or []
    if args.topic:
        topics.append(args.topic)
    if not topics:
        parser.error("No topics provided")

    # Collect modes
    modes = []
    if args.analyze:
        modes.append("analyze")
    if args.patterns:
        modes.append("patterns")
    if args.best_practices:
        modes.append("best-practices")
    if not modes:
        parser.error("At least one mode required: -a, -p, or -b")

    # Validate
    if args.force and args.skip:
        parser.error("Cannot combine --force and --skip")
    if not 1 <= args.workers <= MAX_WORKERS:
        parser.error(f"Workers must be 1-{MAX_WORKERS}")
    if args.iterations < 1:
        parser.error("Iterations must be >= 1")
    if args.max_depth < 1:
        parser.error("Max depth must be >= 1")

    args.topics = topics
    args.modes = modes
    return args


def main() -> None:
    args = parse_args()
    start_time = datetime.now()
    logger = setup_logging(args.verbose)  # Basic console logging first

    try:
        root = find_project_root()
        logger = setup_logging(args.verbose, root)  # Add file logging
        print_banner(args.modes, args.topics, args.workers, args.iterations)
        logger.info(f"{Icons.FOLDER} Project: {C.WHITE}{root}{C.RESET}")

        total_success, all_failed = 0, []

        for mode in args.modes:
            # Only use iterations for analyze mode
            iterations = args.iterations if mode == "analyze" else 1
            max_depth = args.max_depth if mode == "analyze" else DEFAULT_MAX_DEPTH

            success, failed = run_mode(
                mode=mode,
                topics=args.topics,
                project_root=root,
                logger=logger,
                workers=args.workers,
                force=args.force,
                skip=args.skip,
                iterations=iterations,
                max_depth=max_depth,
            )
            total_success += success
            all_failed.extend(failed)

        duration = (datetime.now() - start_time).total_seconds()
        print_summary(total_success, len(all_failed), duration)

        if all_failed:
            logger.warning(f"Failed: {', '.join(set(all_failed))}")
            sys.exit(2)
        if total_success == 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}{Icons.WARN} Interrupted{C.RESET}")
        sys.exit(130)
    except FileNotFoundError as e:
        print(f"{C.RED}{Icons.CROSS} {e}{C.RESET}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
