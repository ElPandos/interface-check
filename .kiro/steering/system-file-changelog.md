---
title:        Changelog Update Requirements
inclusion:    always
version:      1.0
last-updated: 2026-01-15 16:30:00
status:       active
---

# Changelog Update Requirements

## Purpose
Ensure all project changes are documented in CHANGELOG.md for transparency, traceability, and team communication.

## Mandatory Behavior

**When modifying ANY project file, you MUST update CHANGELOG.md under the `[Unreleased]` section.**

## Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
## [Unreleased]

### Added
- New features or files

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features or files

### Fixed
- Bug fixes

### Security
- Security-related changes
```

## Entry Guidelines

### What to Log
- **Source code changes**: New files, modified logic, refactoring
- **Configuration changes**: pyproject.toml, JSON configs, agent configs
- **Documentation updates**: README, steering docs, prompts
- **Infrastructure changes**: Build scripts, CI/CD, Docker
- **Dependency updates**: New or updated packages

### What to Skip
- **Trivial changes**: Whitespace, formatting (unless significant)
- **Auto-generated files**: Logs, coverage reports, build artifacts
- **Temporary files**: .pyc, __pycache__, .venv

### Entry Format

**Good entries** (concise, descriptive):
```markdown
### Added
- SSH keepalive thread for connection stability
- Eye scan automation for SLX switches
- Web-based traffic monitoring UI

### Changed
- Refactored connection layer to use context managers
- Updated Pydantic models to v2.12+ syntax

### Fixed
- SSH reconnection logic in multi-hop scenarios
- Memory leak in worker thread cleanup
```

**Bad entries** (too vague or verbose):
```markdown
### Changed
- Updated file
- Fixed bug
- Made improvements to the codebase
```

## Workflow

1. **Make changes** to project files
2. **Update CHANGELOG.md** immediately:
   - Add entry under appropriate category in `[Unreleased]`
   - Use present tense ("Add feature" not "Added feature")
   - Be specific but concise (one line per change)
3. **Group related changes** under single entry when logical

## Release Process

When creating a release:

1. **Move `[Unreleased]` entries** to new version section:
   ```markdown
   ## [0.2.0] - 2026-01-20
   
   ### Added
   - [entries from Unreleased]
   ```

2. **Create new empty `[Unreleased]` section** at top

3. **Update version links** at bottom:
   ```markdown
   [Unreleased]: https://github.com/user/repo/compare/v0.2.0...HEAD
   [0.2.0]: https://github.com/user/repo/compare/v0.1.0...v0.2.0
   ```

## Examples

### Single File Change
```markdown
### Changed
- Updated SLX scanner to cache interface mappings for performance
```

### Multiple Related Changes
```markdown
### Added
- Traffic testing configuration model (TrafficConfig)
- Iperf server and client wrappers
- Web UI for real-time bandwidth monitoring
```

### Bug Fix
```markdown
### Fixed
- SSH connection timeout in multi-hop scenarios with slow jump hosts
```

### Breaking Change
```markdown
### Changed
- **BREAKING**: Renamed `Host.ip` to `Host.address` in config models
```

## Enforcement

- **Review CHANGELOG.md** before committing changes
- **Verify entries exist** for all modified files
- **Keep entries current** - don't batch multiple sessions into one entry

## Version History

- v1.0 (2026-01-15 16:30:00): Initial changelog requirements
