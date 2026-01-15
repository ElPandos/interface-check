"""Tests for scripts/research_steering.py."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
from unittest.mock import MagicMock

from scripts.research_steering import (
    MODE_COLORS,
    C,
    Icons,
    build_prompt,
    bump_version,
    extract_baseline_urls,
    extract_content,
    extract_endpoints,
    get_steering_path,
    get_tracking_path,
    load_endpoints,
    sanitize_filename,
    save_endpoints,
    strip_ansi,
)

# ──────────────────────────────────────────────────────────────────────────────
# sanitize_filename
# ──────────────────────────────────────────────────────────────────────────────


class TestSanitizeFilename:
    def test_simple_topic(self):
        assert sanitize_filename("docker") == "docker"

    def test_spaces_to_underscores(self):
        assert sanitize_filename("docker compose") == "docker_compose"

    def test_multiple_spaces(self):
        assert sanitize_filename("docker   compose   test") == "docker_compose_test"

    def test_dots_to_underscores(self):
        assert sanitize_filename("docker.compose") == "docker_compose"

    def test_url_stripping(self):
        # The regex removes "https?://" but the colon and slashes are handled separately
        result = sanitize_filename("https://example.com/path")
        assert "example" in result
        assert "com" in result
        assert "path" in result

    def test_special_chars_removed(self):
        assert sanitize_filename('test<>:"/\\|?*file') == "testfile"

    def test_consecutive_underscores_collapsed(self):
        assert sanitize_filename("test___file") == "test_file"

    def test_leading_trailing_underscores_stripped(self):
        assert sanitize_filename("_test_") == "test"
        assert sanitize_filename("___test___") == "test"

    def test_truncation_at_100_chars(self):
        long_topic = "a" * 150
        result = sanitize_filename(long_topic)
        assert len(result) == 100

    def test_truncation_removes_trailing_underscore(self):
        # 99 a's + underscore at position 100 should be stripped
        topic = "a" * 99 + "_b"
        result = sanitize_filename(topic)
        assert not result.endswith("_")

    def test_empty_string_returns_topic(self):
        assert sanitize_filename("") == "topic"
        assert sanitize_filename("   ") == "topic"

    def test_only_special_chars_returns_topic(self):
        assert sanitize_filename("<>:?*") == "topic"


# ──────────────────────────────────────────────────────────────────────────────
# strip_ansi
# ──────────────────────────────────────────────────────────────────────────────


class TestStripAnsi:
    def test_removes_color_codes(self):
        text = f"{C.RED}error{C.RESET}"
        assert strip_ansi(text) == "error"

    def test_removes_bold(self):
        text = f"{C.BOLD}bold text{C.RESET}"
        assert strip_ansi(text) == "bold text"

    def test_removes_multiple_codes(self):
        text = f"{C.BOLD}{C.CYAN}styled{C.RESET}"
        assert strip_ansi(text) == "styled"

    def test_preserves_plain_text(self):
        text = "plain text without codes"
        assert strip_ansi(text) == text

    def test_empty_string(self):
        assert strip_ansi("") == ""


# ──────────────────────────────────────────────────────────────────────────────
# extract_baseline_urls
# ──────────────────────────────────────────────────────────────────────────────


class TestExtractBaselineUrls:
    def test_single_url(self):
        result = extract_baseline_urls("https://example.com")
        assert result == {"https://example.com"}

    def test_multiple_urls(self):
        result = extract_baseline_urls("https://a.com https://b.com")
        assert result == {"https://a.com", "https://b.com"}

    def test_url_with_trailing_punctuation(self):
        result = extract_baseline_urls("Check https://example.com.")
        assert result == {"https://example.com"}

    def test_url_with_multiple_punctuation(self):
        result = extract_baseline_urls("See https://example.com!!!")
        assert result == {"https://example.com"}

    def test_no_urls(self):
        result = extract_baseline_urls("no urls here")
        assert result == set()

    def test_http_and_https(self):
        result = extract_baseline_urls("http://a.com https://b.com")
        assert result == {"http://a.com", "https://b.com"}


# ──────────────────────────────────────────────────────────────────────────────
# extract_content
# ──────────────────────────────────────────────────────────────────────────────


class TestExtractContent:
    def test_yaml_frontmatter(self):
        content = """---
title:        Test
inclusion:    always
version:      1.0
last-updated: 2026-01-14
status:       active
---

# Test Content
"""
        result = extract_content(content)
        assert result is not None
        assert result.startswith("---")
        assert "title:" in result

    def test_yaml_frontmatter_with_leading_text(self):
        content = """Some preamble text
---
title:        Test
inclusion:    always
version:      1.0
last-updated: 2026-01-14
status:       active
---

# Test Content
"""
        result = extract_content(content)
        assert result is not None
        assert result.startswith("---")

    def test_markdown_heading_without_frontmatter(self):
        content = """# Docker Patterns

## Core Principles
Content here
"""
        result = extract_content(content)
        assert result is not None
        assert result.startswith("# Docker Patterns")

    def test_summary_response_heres_what_i_found(self):
        content = """Here's what I found about Docker:

1. Docker is a containerization platform
2. It uses images and containers
"""
        result = extract_content(content)
        assert result is None

    def test_summary_response_numbered_list(self):
        content = """[1. Docker Best Practices](https://example.com)
[2. Container Patterns](https://example.com)
"""
        result = extract_content(content)
        assert result is None

    def test_research_output_heading_rejected(self):
        content = """# Research Output - 2026-01-14

Some research content
"""
        result = extract_content(content)
        assert result is None

    def test_empty_content(self):
        result = extract_content("")
        assert result is None

    def test_whitespace_only(self):
        result = extract_content("   \n\n   ")
        assert result is None

    def test_incomplete_frontmatter(self):
        content = """---
title: Test
---
"""
        # Missing inclusion and version
        result = extract_content(content)
        assert result is None

    def test_logger_called_on_summary(self):
        logger = MagicMock()
        content = "Here's what I found: nothing useful"
        extract_content(content, logger)
        logger.debug.assert_called()


# ──────────────────────────────────────────────────────────────────────────────
# bump_version
# ──────────────────────────────────────────────────────────────────────────────


class TestBumpVersion:
    def test_increments_minor_version(self):
        content = """---
title:        Test
version:      1.0
last-updated: 2026-01-01
---
"""
        result, new_ver = bump_version(content, "2026-01-14")
        assert new_ver == "1.1"
        assert "version:      1.1" in result

    def test_updates_date(self):
        content = """---
title:        Test
version:      1.0
last-updated: 2026-01-01
---
"""
        result, _ = bump_version(content, "2026-01-14")
        assert "last-updated: 2026-01-14" in result

    def test_adds_version_history_entry(self):
        content = """---
title:        Test
version:      1.0
last-updated: 2026-01-01
---

## Version History

- v1.0 (2026-01-01): Initial version
"""
        result, _ = bump_version(content, "2026-01-14")
        assert "v1.1 (2026-01-14): Updated from latest research" in result

    def test_creates_version_history_if_missing(self):
        content = """---
title:        Test
version:      1.0
last-updated: 2026-01-01
---

# Content
"""
        result, _ = bump_version(content, "2026-01-14")
        assert "## Version History" in result
        assert "v1.1 (2026-01-14)" in result

    def test_handles_higher_versions(self):
        content = """---
version:      2.5
---
"""
        result, new_ver = bump_version(content, "2026-01-14")
        assert new_ver == "2.6"

    def test_missing_version_defaults_to_1_0(self):
        content = """---
title: Test
---
"""
        _, new_ver = bump_version(content, "2026-01-14")
        assert new_ver == "1.1"


# ──────────────────────────────────────────────────────────────────────────────
# extract_endpoints
# ──────────────────────────────────────────────────────────────────────────────


class TestExtractEndpoints:
    def test_extracts_relative_paths(self):
        content = "See https://example.com/docs/api for more info"
        result = extract_endpoints(content, "https://example.com")
        assert "/docs/api" in result

    def test_ignores_different_domain(self):
        content = "See https://other.com/path"
        result = extract_endpoints(content, "https://example.com")
        assert len(result) == 0

    def test_respects_max_depth(self):
        content = "https://example.com/a/b/c/d/e"
        result = extract_endpoints(content, "https://example.com", max_depth=2)
        assert "/a/b/c/d/e" not in result

    def test_includes_within_depth(self):
        content = "https://example.com/a/b"
        result = extract_endpoints(content, "https://example.com", max_depth=3)
        assert "/a/b" in result

    def test_strips_trailing_punctuation(self):
        content = "Check https://example.com/path."
        result = extract_endpoints(content, "https://example.com")
        assert "/path" in result

    def test_handles_base_path(self):
        content = "https://example.com/docs/api/v1"
        result = extract_endpoints(content, "https://example.com/docs")
        assert "/api/v1" in result

    def test_empty_content(self):
        result = extract_endpoints("", "https://example.com")
        assert len(result) == 0


# ──────────────────────────────────────────────────────────────────────────────
# get_steering_path
# ──────────────────────────────────────────────────────────────────────────────


class TestGetSteeringPath:
    def test_returns_correct_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = get_steering_path(root, "docker", "patterns")
            assert path == root / ".kiro" / "steering" / "docker_patterns.md"

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = get_steering_path(root, "test", "best-practices")
            assert path.parent.exists()

    def test_sanitizes_topic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = get_steering_path(root, "docker compose", "patterns")
            assert "docker_compose" in path.name


# ──────────────────────────────────────────────────────────────────────────────
# get_tracking_path
# ──────────────────────────────────────────────────────────────────────────────


class TestGetTrackingPath:
    def test_returns_correct_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = get_tracking_path(root, "https://example.com")
            today = datetime.now().strftime("%Y-%m-%d")
            assert today in str(path)
            assert "endpoints" in str(path)
            assert path.suffix == ".json"

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = get_tracking_path(root, "test")
            assert path.parent.exists()


# ──────────────────────────────────────────────────────────────────────────────
# load_endpoints / save_endpoints
# ──────────────────────────────────────────────────────────────────────────────


class TestEndpointPersistence:
    def test_load_empty_when_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = load_endpoints(root, "nonexistent")
            assert result == set()

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            endpoints = {"/api/v1", "/docs"}
            save_endpoints(root, "test", 1, endpoints)
            loaded = load_endpoints(root, "test")
            assert endpoints == loaded

    def test_save_incremental(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            save_endpoints(root, "test", 1, {"/api"})
            save_endpoints(root, "test", 2, {"/docs"})
            loaded = load_endpoints(root, "test")
            assert loaded == {"/api", "/docs"}

    def test_save_skips_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            save_endpoints(root, "test", 1, {"/api"})
            save_endpoints(root, "test", 2, {"/api"})  # Duplicate
            path = get_tracking_path(root, "test")
            data = json.loads(path.read_text())
            # Should only have iteration_1
            assert "iteration_1" in data
            assert "iteration_2" not in data


# ──────────────────────────────────────────────────────────────────────────────
# build_prompt
# ──────────────────────────────────────────────────────────────────────────────


class TestBuildPrompt:
    def test_patterns_prompt(self):
        prompt = build_prompt("docker", "patterns")
        assert "patterns" in prompt.lower()
        assert "anti-patterns" in prompt.lower()
        assert "docker_patterns.md" in prompt

    def test_best_practices_prompt(self):
        prompt = build_prompt("kubernetes", "best-practices")
        assert "best practices" in prompt.lower()
        assert "kubernetes_best-practices.md" in prompt

    def test_analyze_prompt(self):
        prompt = build_prompt("https://example.com", "analyze")
        assert "analysis" in prompt.lower()
        assert "analyze" in prompt

    def test_includes_frontmatter_template(self):
        prompt = build_prompt("test", "patterns")
        assert "---" in prompt
        assert "title:" in prompt
        assert "inclusion:" in prompt
        assert "version:" in prompt

    def test_includes_excluded_urls(self):
        excluded = {"https://example.com/old"}
        prompt = build_prompt("test", "analyze", excluded)
        assert "Avoid already researched" in prompt
        assert "https://example.com/old" in prompt

    def test_topic_title_case(self):
        prompt = build_prompt("docker-compose", "patterns")
        assert "Docker-Compose" in prompt or "Docker Compose" in prompt


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────


class TestConstants:
    def test_mode_colors_defined(self):
        assert "analyze" in MODE_COLORS
        assert "patterns" in MODE_COLORS
        assert "best-practices" in MODE_COLORS

    def test_icons_are_strings(self):
        assert isinstance(Icons.ROCKET, str)
        assert isinstance(Icons.CHECK, str)
        assert isinstance(Icons.CROSS, str)

    def test_colors_are_escape_sequences(self):
        assert C.RESET.startswith("\033[")
        assert C.BOLD.startswith("\033[")
        assert C.RED.startswith("\033[")
