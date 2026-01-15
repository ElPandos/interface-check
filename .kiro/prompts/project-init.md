---
title:        Project Initialization Instructions
inclusion:    always
version:      1.0
last-updated: 2026-01-15 15:25:00
status:       active
---

# Project init: Initialize Project Context

## Objective
Build comprehensive understanding of the codebase through systematic analysis of structure, documentation, and key files.

## Process

### 1. Project Structure Analysis
**Primary Structure Discovery:**
```bash
# Check if git repository
git status 2>/dev/null && echo "Git repository detected" || echo "Not a git repository"

# List project structure (try multiple approaches for robustness)
if command -v tree >/dev/null 2>&1; then
    tree -L 3 -I 'node_modules|__pycache__|.git|dist|build|.venv|venv|target|.next'
else
    find . -maxdepth 3 -type d -not -path '*/.*' -not -path '*/node_modules*' -not -path '*/__pycache__*' | head -20
fi
```

**File Discovery (if git repository):**
```bash
# Get tracked files by category
git ls-files | grep -E '\.(py|js|ts|jsx|tsx|rs|go|java|cpp|c|h)$' | head -20
git ls-files | grep -E '\.(json|toml|yaml|yml|md|txt)$' | head -10
```

### 2. Core Documentation Review
**Priority Order:**
1. **README.md** (project root) - Essential project overview
2. **docs/** directory contents - Architecture and setup guides
3. **.kiro/steering/** documents - Project-specific best practices (already in context)
4. **CHANGELOG.md** or **HISTORY.md** - Recent changes
5. **CONTRIBUTING.md** - Development guidelines

**Skip:** examples/, samples/, content_plan/, test_data/, fixtures/

### 3. Configuration and Entry Points
**Essential Files (read in order of importance):**
1. **Package/Project Config:** pyproject.toml, package.json, Cargo.toml, go.mod, pom.xml
2. **Main Entry Points:** main.py, app.py, index.js, index.ts, src/main.*, cmd/main.go
3. **Build/Dev Config:** Dockerfile, docker-compose.yml, Makefile, .github/workflows/
4. **Environment Config:** .env.example, config/, settings/

### 4. Code Architecture Discovery
**Key Patterns to Identify:**
- **src/** or **lib/** structure and organization
- **models/** or **schemas/** - Data structures
- **services/** or **handlers/** - Business logic
- **tests/** structure and framework
- **scripts/** or **tools/** - Automation

### 5. Current State Assessment
**Git Repository Analysis:**
```bash
# Current state
git branch --show-current 2>/dev/null
git status --porcelain 2>/dev/null

# Recent activity (last 5 commits)
git log -5 --oneline --no-merges 2>/dev/null

# Active files (recently modified)
git log -10 --name-only --pretty=format: | sort | uniq -c | sort -nr | head -10 2>/dev/null
```

## Error Handling
- If commands fail, continue with alternative approaches
- Use `2>/dev/null` to suppress error messages
- Provide fallback methods for each discovery step
- Report what information is unavailable rather than failing

## Output Report Format

### 🎯 Project Overview
- **Purpose:** [Application type and primary function]
- **Scale:** [Size indicators: files, directories, complexity]
- **Status:** [Development stage, version if available]

### 🏗️ Architecture & Structure
- **Pattern:** [MVC, microservices, monolith, etc.]
- **Organization:** [Key directories and their roles]
- **Entry Points:** [Main files and how they connect]

### 🛠️ Technology Stack
- **Languages:** [Primary and secondary languages with versions]
- **Frameworks:** [Major frameworks and libraries]
- **Tools:** [Build tools, package managers, testing frameworks]
- **Infrastructure:** [Docker, databases, external services]

### 📋 Development Practices
- **Code Style:** [Formatting, linting, conventions observed]
- **Testing:** [Framework, coverage approach, test organization]
- **Documentation:** [Level and style of documentation]
- **CI/CD:** [Automation and deployment practices]

### 📊 Current State
- **Branch:** [Active branch if git repository]
- **Recent Focus:** [Recent commits and active development areas]
- **Health:** [Any immediate issues or concerns noted]

### ⚠️ Key Observations
- **Strengths:** [Well-implemented aspects]
- **Areas for Attention:** [Potential improvements or concerns]
- **Missing Elements:** [Standard files or practices not found]

**Use bullet points, keep sections concise, highlight critical information.**

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.1 (2026-01-12 00:00:00): Optimized for better robustness and efficiency
