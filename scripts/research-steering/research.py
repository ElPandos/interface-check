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


def filter_endpoints_by_depth(endpoints: set[str], max_depth: int) -> set[str]:
    """Filter endpoints by maximum depth from baseline."""
    filtered = set()
    for endpoint in endpoints:
        # Count depth by number of path segments (excluding empty ones)
        depth = len([seg for seg in endpoint.split('/') if seg.strip()])
        if depth <= max_depth:
            filtered.add(endpoint)
    return filtered


def extract_endpoints_from_content(content: str, baseline_url: str, max_depth: int = 3) -> set[str]:
    """Extract relative endpoints from content based on baseline URL."""
    from urllib.parse import urlparse
    
    parsed_baseline = urlparse(baseline_url)
    base_domain = f"{parsed_baseline.scheme}://{parsed_baseline.netloc}"
    base_path = parsed_baseline.path.rstrip('/')
    
    # Find all URLs matching the baseline domain with improved regex
    url_pattern = r"https?://[^\s\]<>\"'(),]+"
    urls = re.findall(url_pattern, content)
    endpoints = set()
    
    for url in urls:
        # Clean up any trailing punctuation
        url = url.rstrip('.,;:!?')
        
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc == parsed_baseline.netloc:
                path = parsed_url.path.rstrip('/')
                if path.startswith(base_path) and path != base_path:
                    relative_path = path[len(base_path):] if base_path else path
                    # Only add valid paths (not empty, not just punctuation)
                    if relative_path and len(relative_path) > 1 and not relative_path.isspace():
                        endpoints.add(relative_path)
        except Exception:
            # Skip malformed URLs
            continue
    
    # Filter by depth
    return filter_endpoints_by_depth(endpoints, max_depth)


def save_endpoint_tracking(project_root: Path, topic: str, iteration: int, endpoints: set[str]) -> None:
    """Save discovered endpoints to tracking file."""
    import json
    
    safe_topic = sanitize_filename(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    tracking_dir = project_root / ".kiro" / "research" / today / "analyze" / "endpoints"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    
    tracking_file = tracking_dir / f"{safe_topic}_endpoints.json"
    
    # Load existing data
    tracking_data = {}
    all_existing_endpoints = set()
    if tracking_file.exists():
        try:
            tracking_data = json.loads(tracking_file.read_text())
            # Collect all previously discovered endpoints
            for iteration_data in tracking_data.values():
                if isinstance(iteration_data, dict) and "endpoints" in iteration_data:
                    all_existing_endpoints.update(iteration_data["endpoints"])
        except Exception:
            tracking_data = {}
    
    # Only save NEW endpoints (not already discovered)
    new_endpoints = endpoints - all_existing_endpoints
    
    # Only add entry if there are new endpoints
    if new_endpoints:
        tracking_data[f"iteration_{iteration}"] = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": sorted(list(new_endpoints))
        }
        
        # Save updated data
        tracking_file.write_text(json.dumps(tracking_data, indent=2))


def load_discovered_endpoints(project_root: Path, topic: str) -> set[str]:
    """Load all previously discovered endpoints."""
    import json
    
    safe_topic = sanitize_filename(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    tracking_file = project_root / ".kiro" / "research" / today / "analyze" / "endpoints" / f"{safe_topic}_endpoints.json"
    
    if not tracking_file.exists():
        return set()
    
    try:
        tracking_data = json.loads(tracking_file.read_text())
        all_endpoints = set()
        
        for iteration_data in tracking_data.values():
            if isinstance(iteration_data, dict) and "endpoints" in iteration_data:
                all_endpoints.update(iteration_data["endpoints"])
        
        return all_endpoints
    except Exception:
        return set()


def create_iteration_filename(topic: str, iteration: int) -> str:
    """Create filename for specific iteration in research folder."""
    safe_topic = sanitize_filename(topic)
    # Limit base name length to leave room for iteration suffix
    if len(safe_topic) > 80:
        safe_topic = safe_topic[:80].rstrip('_')
    return f"{safe_topic}_iter{iteration}_analyze.md"


def get_iteration_path(project_root: Path, topic: str, iteration: int) -> Path:
    """Get path for iteration file in research folder."""
    iter_filename = create_iteration_filename(topic, iteration)
    today = datetime.now().strftime("%Y-%m-%d")
    research_dir = project_root / ".kiro" / "research" / today / "analyze"
    research_dir.mkdir(parents=True, exist_ok=True)
    return research_dir / iter_filename


def cleanup_iteration_files(project_root: Path, topic: str, total_iterations: int, logger: logging.Logger) -> None:
    """Clean up iteration files after merging."""
    logger.info("Cleaning up iteration files...")
    
    cleaned_count = 0
    for i in range(1, total_iterations + 1):
        iter_path = get_iteration_path(project_root, topic, i)
        if iter_path.exists():
            try:
                iter_path.unlink()
                cleaned_count += 1
                logger.debug(f"Removed iteration file: {iter_path.name}")
            except Exception as e:
                logger.warning(f"Failed to remove {iter_path.name}: {e}")
    
    # Also clean up endpoint tracking file
    safe_topic = sanitize_filename(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    tracking_file = project_root / ".kiro" / "research" / today / "analyze" / "endpoints" / f"{safe_topic}_endpoints.json"
    if tracking_file.exists():
        try:
            tracking_file.unlink()
            logger.debug(f"Removed endpoint tracking file: {tracking_file.name}")
        except Exception as e:
            logger.warning(f"Failed to remove endpoint tracking: {e}")
    
    logger.info(f"Cleaned up {cleaned_count} iteration files")


def merge_iteration_files(project_root: Path, topic: str, total_iterations: int, logger: logging.Logger) -> Path:
    """Merge all iteration files into final steering document."""
    import json
    
    safe_topic = sanitize_filename(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    research_dir = project_root / ".kiro" / "research" / today / "analyze"
    final_path = research_dir / f"{safe_topic}_analyze.md"
    
    logger.info(f"Merging {total_iterations} iteration files into final document")
    
    # Collect iteration files from research folder
    iteration_files = []
    for i in range(1, total_iterations + 1):
        iter_path = get_iteration_path(project_root, topic, i)
        if iter_path.exists():
            iteration_files.append((i, iter_path))
    
    if not iteration_files:
        logger.warning("No iteration files found to merge")
        return final_path
    
    # Load endpoint tracking
    safe_topic = sanitize_filename(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    tracking_file = project_root / ".kiro" / "research" / today / "analyze" / "endpoints" / f"{safe_topic}_endpoints.json"
    all_endpoints = set()
    if tracking_file.exists():
        try:
            tracking_data = json.loads(tracking_file.read_text())
            for iteration_data in tracking_data.values():
                if isinstance(iteration_data, dict) and "endpoints" in iteration_data:
                    all_endpoints.update(iteration_data["endpoints"])
        except Exception:
            pass
    
    # Create merged document
    today = datetime.now().strftime("%Y-%m-%d")
    merged_content = [
        "---",
        f"title:        {topic[:50]}... Analysis (Merged)",
        "inclusion:    always",
        "version:      1.0",
        f"last-updated: {today}",
        "status:       active",
        "---",
        "",
        f"# {topic[:50]}... Analysis",
        "",
        "*This document was created by merging multiple research iterations.*",
        ""
    ]
    
    # Add content from each iteration
    for iteration, iter_path in iteration_files:
        logger.debug(f"Processing iteration {iteration} file: {iter_path.name}")
        
        try:
            content = iter_path.read_text(encoding="utf-8")
            
            # Extract main content (skip frontmatter)
            lines = content.split('\n')
            content_start = 0
            for i, line in enumerate(lines):
                if line.strip() == '---' and i > 0:
                    content_start = i + 1
                    break
            
            if content_start > 0:
                iteration_content = '\n'.join(lines[content_start:]).strip()
                merged_content.extend([
                    f"## Iteration {iteration} Findings",
                    "",
                    iteration_content,
                    ""
                ])
        
        except Exception as e:
            logger.warning(f"Failed to process iteration {iteration}: {e}")
    
    # Add endpoint summary
    if all_endpoints:
        merged_content.extend([
            "## Discovered Endpoints",
            "",
            "The following endpoints were discovered during research:",
            ""
        ])
        for endpoint in sorted(all_endpoints):
            merged_content.append(f"- `{endpoint}`")
        merged_content.append("")
    
    # Add version history
    merged_content.extend([
        "## Version History",
        "",
        f"- v1.0 ({today}): Merged analysis from {len(iteration_files)} research iterations",
        ""
    ])
    
    # Write merged file to steering folder
    final_path.write_text('\n'.join(merged_content), encoding="utf-8")
    
    logger.info(f"Created merged document: {final_path.name}")
    logger.info(f"Discovered {len(all_endpoints)} unique endpoints across all iterations")
    
    # Clean up iteration files after successful merge
    cleanup_iteration_files(project_root, topic, total_iterations, logger)
    
    return final_path
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


def debug_source_extraction(content: str, logger: logging.Logger, index: str = "") -> set[str]:
    """Debug version of extract_existing_sources with detailed logging."""
    logger.debug(f"{index}=== SOURCE EXTRACTION DEBUG ===")
    logger.debug(f"{index}Content length: {len(content)} chars")
    
    # Show last few lines to see if sources are at the end
    lines = content.split('\n')
    logger.debug(f"{index}First 10 lines: {lines[:10]}")
    logger.debug(f"{index}Last 10 lines: {lines[-10:]}")
    
    sources = set()
    
    # Look for Sources/References section with more flexible patterns
    patterns = [
        r"(?i)## Sources?\s*&?\s*References?\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)## References?\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)References:\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)## Sources?\s*\n(.*?)(?=\n##|\Z)",
        r"(?i)Sources:\s*\n(.*?)(?=\n##|\Z)",
        # Look for any section that might contain URLs
        r"(?i)## .*(?:source|reference|link).*\n(.*?)(?=\n##|\Z)",
    ]
    
    for i, pattern in enumerate(patterns):
        logger.debug(f"{index}Trying pattern {i+1}: {pattern[:50]}...")
        match = re.search(pattern, content, re.DOTALL)
        if match:
            refs_section = match.group(1)
            logger.debug(f"{index}Found references section (length: {len(refs_section)}): {refs_section[:200]}...")
            
            # Extract URLs from markdown links and plain URLs
            url_patterns = [
                r"\[.*?\]\((https?://[^\)]+)\)",  # [text](url)
                r"https?://[^\s\]]+",             # plain URLs
            ]
            for j, url_pattern in enumerate(url_patterns):
                urls = re.findall(url_pattern, refs_section)
                logger.debug(f"{index}URL pattern {j+1} found {len(urls)} URLs: {urls[:3]}...")
                sources.update(urls)
            break
        else:
            logger.debug(f"{index}Pattern {i+1} no match")
    
    if not sources:
        logger.debug(f"{index}No sources found in sections. Checking for any URLs in entire content...")
        all_urls = re.findall(r"https?://[^\s\]<>\"']+", content)
        logger.debug(f"{index}All URLs in content ({len(all_urls)}): {all_urls[:5]}...")
        
        # If we find URLs but no proper references section, use the URLs we found
        if all_urls:
            logger.debug(f"{index}Using URLs found in content as sources")
            sources.update(all_urls)
    
    logger.debug(f"{index}Final extracted sources ({len(sources)}): {list(sources)[:5]}...")
    logger.debug(f"{index}=== END SOURCE EXTRACTION DEBUG ===")
    
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


def build_prompt(topic: str, research_type: str, existing_sources: set[str] | None = None, discovered_endpoints: set[str] | None = None) -> str:
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
            base_prompt += f" Explore deeper into the baseline sites ({', '.join(baseline_urls)}) to find additional subpages, documentation sections, or related content that haven't been covered yet."
        
        # Add discovered endpoints as additional starting points
        if discovered_endpoints:
            baseline_url = list(baseline_urls)[0] if baseline_urls else ""
            endpoint_urls = [f"{baseline_url.rstrip('/')}{endpoint}" for endpoint in list(discovered_endpoints)[:5]]
            base_prompt += f" Also explore these discovered pages for deeper content: {', '.join(endpoint_urls)}."
        
        # Exclude already researched URLs
        excluded_urls = [url for url in existing_sources if url.startswith('http')]
        if excluded_urls:
            exclusion = f" IMPORTANT: Avoid these already researched URLs: {', '.join(excluded_urls[:5])}{'...' if len(excluded_urls) > 5 else ''}. Find NEW pages, subpages, and sections from the same sites or related sources. Go deeper into the site structure to find content not yet analyzed."
            base_prompt += exclusion
        else:
            # If no existing sources, encourage comprehensive exploration
            base_prompt += " Thoroughly explore all subpages, documentation sections, and related content."
    else:
        # For first-time research, encourage comprehensive exploration
        base_prompt += " Thoroughly explore all subpages, documentation sections, and related content."

    # CRITICAL: Always require source references
    base_prompt += " IMPORTANT: Include a '## Sources & References' section at the end with all URLs you researched, formatted as: [Description](URL) — Brief note about content accessed YYYY-MM-DD"

    # Use sanitized filename for research document
    safe_topic = sanitize_filename(topic)
    research_name = f"{safe_topic}_{research_type}.md"
    return f"{base_prompt} Save your research analysis to a markdown file."


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

    logger.debug(f"{index}Checking steering file: {steering_path}")
    
    if not steering_path.exists():
        logger.debug(f"{index}File doesn't exist, creating new file")
        steering_path.write_text(new_content, encoding="utf-8")
        logger.info(f"{index}✓ Created: {steering_path.name}")
        return True
        
    if force:
        logger.debug(f"{index}Force flag set, overwriting existing file")
        steering_path.write_text(new_content, encoding="utf-8")
        logger.info(f"{index}✓ Force overwritten: {steering_path.name}")
        return True

    existing = steering_path.read_text(encoding="utf-8")
    logger.debug(f"{index}Comparing content lengths: existing={len(existing)}, new={len(new_content)}")

    # Skip if identical
    if existing.strip() == new_content.strip():
        logger.info(f"{index}⚪ No change needed: {steering_path.name}")
        return True  # This should be SUCCESS, not failure!

    logger.debug(f"{index}Content differs, updating with version bump")
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
    iteration: int = 1,
) -> tuple[str, bool, float]:
    """Run single research task."""
    start = datetime.now()

    try:
        # Use iteration-specific filename in research folder
        steering_path = get_iteration_path(project_root, topic, iteration)
        logger.debug(f"{index}Iteration {iteration} file: {steering_path}")

        # Early skip check
        if skip_if_exists and steering_path.is_file():
            logger.info(f"{index}⏭ Skipped (already exists): {topic}")
            return topic, True, 0.0

        # Load previously discovered endpoints for exclusion
        discovered_endpoints = load_discovered_endpoints(project_root, topic)
        logger.debug(f"{index}Previously discovered endpoints ({len(discovered_endpoints)}): {list(discovered_endpoints)[:5]}...")

        # Build exclusion list from discovered endpoints
        baseline_urls = extract_baseline_urls(topic)
        excluded_urls = set()
        if baseline_urls and discovered_endpoints:
            baseline_url = list(baseline_urls)[0]
            # Convert relative endpoints back to full URLs for exclusion
            for endpoint in discovered_endpoints:
                excluded_urls.add(f"{baseline_url.rstrip('/')}{endpoint}")

        prompt = build_prompt(topic, research_type, excluded_urls if excluded_urls else None, discovered_endpoints)
        logger.debug(f"{index}Generated prompt length: {len(prompt)} chars")
        logger.debug(f"{index}Excluding {len(excluded_urls)} URLs from previous iterations")
        
        cmd = ["kiro-cli", "chat", "--trust-all-tools", "--no-interactive", prompt]
        logger.debug(f"{index}Running command: {' '.join(cmd[:4])}...")

        logger.info(f"{index}→ Researching {research_type} (iteration {iteration}): {topic}")

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
        logger.debug(f"{index}Command completed in {duration:.1f}s, stdout length: {len(result.stdout)}")

        # Clean ANSI escape sequences from output
        clean_output = strip_ansi_codes(result.stdout.strip())

        if not clean_output:
            logger.warning(f"{index}⚠ No output received for {topic}")
            return topic, False, duration

        # Extract only the steering document content from kiro-cli output
        content = extract_steering_content(clean_output)
        logger.debug(f"{index}Extracted content length: {len(content)} chars")

        # Extract endpoints from the generated content
        new_endpoints = set()
        if baseline_urls:
            baseline_url = list(baseline_urls)[0]
            discovered_endpoints = extract_endpoints_from_content(content, baseline_url)
            
            # Load existing endpoints to filter duplicates
            existing_endpoints = load_discovered_endpoints(project_root, topic)
            new_endpoints = discovered_endpoints - existing_endpoints
            
            logger.debug(f"{index}Total discovered: {len(discovered_endpoints)}, existing: {len(existing_endpoints)}, new: {len(new_endpoints)}")
            logger.debug(f"{index}New unique endpoints: {list(new_endpoints)[:5]}...")
            
            # Save endpoint tracking (only saves if there are new endpoints)
            save_endpoint_tracking(project_root, topic, iteration, discovered_endpoints)

        updated = update_or_create_steering(steering_path, content, logger, index, force=force)
        logger.debug(f"{index}File operation result: {updated}")

        logger.info(f"{index}✓ Done in {duration:.1f}s → {steering_path.name}")
        logger.info(f"{index}📍 Discovered {len(new_endpoints)} new endpoints in iteration {iteration}")
        
        return topic, updated, duration

    except subprocess.TimeoutExpired:
        logger.error(f"{index}✗ Timeout ({TIMEOUT_SEC}s): {topic}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{index}✗ kiro-cli failed for {topic}: {e.returncode}")
        if e.stderr:
            logger.debug(f"{index}stderr: {e.stderr.strip()}")
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
        "-d",
        "--max-depth",
        type=int,
        default=3,
        help="maximum URL depth from baseline (default: 3)",
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


def has_new_sources_available(topic: str, research_type: str, project_root: Path, logger: logging.Logger) -> bool:
    """Check if there are potentially new sources to research."""
    if research_type != "analyze":
        logger.debug(f"Non-analyze mode ({research_type}), assuming sources available")
        return True
    
    # Check discovered endpoints count
    discovered_endpoints = load_discovered_endpoints(project_root, topic)
    baseline_urls = extract_baseline_urls(topic)
    
    logger.debug(f"Found {len(discovered_endpoints)} existing endpoints, {len(baseline_urls)} baseline URLs")
    
    # If we have baseline URLs but few endpoints, likely more to find
    if baseline_urls and len(discovered_endpoints) < 15:  # Increased threshold
        logger.debug(f"Baseline URLs present with <15 endpoints, more likely available")
        return True
        
    # If no baseline URLs, assume more sources available
    if not baseline_urls:
        logger.debug(f"No baseline URLs found, assuming sources available")
        return True
        
    has_sources = len(discovered_endpoints) < 20  # Higher threshold for endpoint-based tracking
    logger.debug(f"Endpoint threshold check: {len(discovered_endpoints)}/20, available={has_sources}")
    return has_sources


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
    topics_with_sources = []
    for topic in topics:
        has_sources = has_new_sources_available(topic, research_type, project_root, logger)
        logger.debug(f"Topic '{topic[:50]}...' has sources available: {has_sources}")
        if has_sources:
            topics_with_sources.append(topic)
    
    if not topics_with_sources:
        logger.info("No topics have new sources available. Stopping iterations.")
        return 0, [], True  # success_count, failed, should_stop
    
    if len(topics_with_sources) < len(topics):
        skipped = len(topics) - len(topics_with_sources)
        logger.info(f"Skipping {skipped} topics with no new sources available")
    
    logger.debug(f"Processing {len(topics_with_sources)} topics with {kwargs.get('workers', DEFAULT_WORKERS)} workers")
    
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
                    iteration=iteration,
                )
                for i, topic in enumerate(topics_with_sources, 1)
            ]

            success_count = 0
            failed = []

            for future in as_completed(futures):
                try:
                    topic, ok, duration = future.result()
                    logger.debug(f"Task completed: topic='{topic[:30]}...', success={ok}, duration={duration:.1f}s")
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
            logger.warning(f"Failed topics in iteration {iteration}: {', '.join([f[:30] + '...' for f in failed])}")
            
        # Stop if all failed (but not if some succeeded)
        should_stop = success_count == 0 and len(failed) > 0
        logger.debug(f"Should stop: success={success_count}, failed={len(failed)}, stop={should_stop}")
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

        # Final summary and merge
        if args.iterations > 1:
            logger.info(f"=== Final Summary ===")
            logger.info(f"Total successful across all iterations: {total_success}")
            
            # Merge iteration files for each topic
            for topic in args.topics:
                try:
                    final_path = merge_iteration_files(root, topic, args.iterations, logger)
                    logger.info(f"📄 Merged final document: {final_path.name}")
                except Exception as e:
                    logger.error(f"Failed to merge files for topic '{topic}': {e}")
            
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
