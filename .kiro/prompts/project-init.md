---
title:        Project Initialization Instructions
inclusion:    always
version:      1.2
last-updated: 2026-01-15 16:27:00
status:       active
---

# Project init: Initialize Project Context

## Objective
Build comprehensive understanding of the interface-check codebase through systematic analysis of structure, documentation, and key files.

## Process

### 1. Project Structure Analysis
**Primary Structure Discovery:**
```bash
# Check git status
git status 2>/dev/null && echo "Git repository detected" || echo "Not a git repository"

# List project structure
if command -v tree >/dev/null 2>&1; then
    tree -L 3 -I 'node_modules|__pycache__|.git|dist|build|.venv|venv|target|.next|logs'
else
    find . -maxdepth 3 -type d -not -path '*/.*' -not -path '*/node_modules*' -not -path '*/__pycache__*' -not -path '*/logs*' | head -30
fi
```

**File Discovery:**
```bash
# Python files
git ls-files | grep -E '\.py$' | head -30

# Configuration files
git ls-files | grep -E '\.(json|toml|yaml|yml|md)$' | head -15
```

### 2. Core Documentation Review
**Priority Order:**
1. **README.md** - Project overview and quick start
2. **.kiro/steering/** - Foundation documents (product, tech, structure)
3. **docs/** - Detailed documentation
4. **AGENTS.md** - Custom agent configurations

**Skip:** examples/, logs/, .ui/, __pycache__/

### 3. Configuration and Entry Points
**Essential Files:**
1. **pyproject.toml** - Dependencies and tool configuration
2. **main.py** - Web GUI entry point
3. **main_scan.py** - Interface scanning entry
4. **main_scan_traffic.py** - Traffic testing entry
5. **main_scan_analyze.py** - Log analysis entry
6. **main_scan_cfg.json** - Scanning configuration
7. **main_scan_traffic_cfg.json** - Traffic configuration

### 4. Code Architecture Discovery
**Key Areas:**
- **src/app.py** - Application initialization
- **src/core/** - Business logic (connect, scanner, traffic, config, log)
- **src/interfaces/** - Abstract interfaces
- **src/models/** - Pydantic data models
- **src/platform/** - Platform-specific tools (ethtool, mlx, mst, rdma)
- **src/ui/** - NiceGUI web interface (tabs, handlers, components)
- **tests/** - Test suite

### 5. Current State Assessment
```bash
# Current branch and status
git branch --show-current 2>/dev/null
git status --porcelain 2>/dev/null

# Recent commits
git log -5 --oneline --no-merges 2>/dev/null

# Recently modified files
git log -10 --name-only --pretty=format: | sort | uniq -c | sort -nr | head -10 2>/dev/null
```

## Error Handling
- Use `2>/dev/null` to suppress errors
- Provide fallback methods for each step
- Continue on failures
- Report unavailable information

## Output Report Format

### 🎯 Project Overview
- **Purpose:** Network interface monitoring and traffic testing tool
- **Type:** SSH-based remote diagnostics with web GUI
- **Scale:** [File count, complexity indicators]
- **Status:** [Version, development stage]

### 🏗️ Architecture & Structure
- **Pattern:** Layered architecture (UI → Core → Platform)
- **Organization:** 
  - Core: Business logic and workers
  - Platform: Tool abstractions
  - UI: NiceGUI web interface
  - Models: Pydantic validation
- **Entry Points:** main.py (GUI), main_scan.py (scanning), main_scan_traffic.py (traffic)

### 🛠️ Technology Stack
- **Language:** Python 3.13
- **Web UI:** NiceGUI 2.24.2 (FastAPI + Vue.js)
- **SSH:** Paramiko 4.0.0+
- **Validation:** Pydantic 2.12+
- **Visualization:** Plotly 6.5+
- **Data:** Pandas 2.3+
- **Tools:** UV (package manager), Ruff (linter), MyPy (type checker), Pytest

### 📋 Development Practices
- **Code Style:** Ruff (line-length: 120), strict type hints
- **Testing:** Pytest with coverage
- **Documentation:** Google-style docstrings
- **Type Checking:** MyPy strict mode
- **Version Control:** Git with .kiro/ configuration

### 📊 Current State
- **Branch:** [Active branch]
- **Recent Focus:** [Recent development areas]
- **Health:** [Issues or concerns]

### ⚠️ Key Observations
- **Strengths:** [Well-implemented features]
- **Areas for Attention:** [Improvements needed]
- **Missing Elements:** [Standard practices not found]

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Optimized for better robustness and efficiency
- v1.2 (2026-01-15 16:27:00): Customized for interface-check project specifics
