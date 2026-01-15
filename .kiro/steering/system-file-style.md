---
title:        System File Style Guidelines
inclusion:    always
version:      1.1
last-updated: 2026-01-12 00:00:00
status:       active
---

# System File Style Guidelines (v1.1)

## Purpose
Enforce a clean, consistent, modern Python style across all project scripts and tools, using `scripts/research-steering/research.py` as the gold standard.

## Core Rules (non-negotiable)

### 1. File Skeleton
```python
#!/usr/bin/env python3
"""
One-line purpose.

Usage:
    command example 1
    command example 2 --flag value
"""

from __future__ import annotations

# stdlib (alpha)
import argparse
import logging
import sys
from pathlib import Path

# third-party (alpha)
from packaging import version

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MAX_WORKERS = 30
DEFAULT_WORKERS = 5
TIMEOUT_SEC = 300

# ──────────────────────────────────────────────────────────────────────────────
# Helpers → Main logic → CLI → Entry point
# ──────────────────────────────────────────────────────────────────────────────
```

### 2. Naming

| Scope | Convention | Example |
|-------|------------|---------|
| Files | kebab-case.py | research.py |
| Functions | snake_case | run_research |
| Constants | UPPER_SNAKE_CASE | MAX_WORKERS |
| Classes | PascalCase | ConfigManager |

### 3. Imports (strict order, alphabetical within group)
- `from __future__ import annotations`
- Standard library
- Third-party
- Local/project imports
→ One module per line, no * imports

### 4. Logging
```python
def setup_logging(verbose: bool = False) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("script-name")
```
→ Use │ separator and fixed-width level for perfect alignment.

### 5. Error Handling Pattern
```python
try:
    result = operation()
    return result, True, duration
except KeyboardInterrupt:
    logger.info("Interrupted by user")
    sys.exit(130)
except SpecificError as e:
    logger.error(f"Failed: {e}")
    return "", False, duration
except Exception as e:  # always last
    logger.exception(f"Unexpected: {e}")
    return "", False, duration
```

### 6. CLI with argparse (standard pattern)
```python
parser = argparse.ArgumentParser(
    description="Short tool description",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""Examples:
  %(prog)s patterns docker redis
  %(prog)s best-practices -t "ui testing" -f
  %(prog)s analyze kubernetes --verbose
""",
)
parser.add_argument("-m", "--mode", choices=["a", "b"], required=True)
parser.add_argument("topics", nargs="*", help="Topics (or use -t)")
parser.add_argument("-t", "--topics-str", help="Space-separated topics")
parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS)
parser.add_argument("-f", "--force", action="store_true")
parser.add_argument("-s", "--skip", action="store_true")
parser.add_argument("-v", "--verbose", action="store_true")
```

### 7. Concurrency (ThreadPoolExecutor)
```python
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    futures = [pool.submit(task, item) for item in items]
    for future in as_completed(futures):
        item, success, dur = future.result()
        # process
```

### 8. Progress Logging (prefix with fixed-width index)
```python
index = f"[{i:2d}/{total}] "
logger.info(f"{index}→ Starting {topic}")
logger.info(f"{index}✓ Done in {dur:.1f}s")
logger.error(f"{index}✗ Failed: {e}")
```

### 9. Type Hints & Returns
- Always use type hints
- Prefer explicit `tuple[str, bool, float]` over ambiguous returns
- Use `-> logging.Logger`, `-> Path`, etc.

### 10. Formatting & Linting
- `ruff format` (line length ≤120)
- `ruff check --fix`
- Trailing commas in multiline structures
- No unused imports/variables

## Quick Checklist (paste into PR description)
- [ ] Shebang + docstring with usage examples
- [ ] `from __future__ import annotations`
- [ ] Imports sorted & grouped
- [ ] Constants section with decorative separator
- [ ] Type hints everywhere
- [ ] Structured error handling + duration tracking
- [ ] Clean logging with │ and index prefix
- [ ] `ruff format` passed

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Condensed, removed duplication, added checklist, stricter import rules
