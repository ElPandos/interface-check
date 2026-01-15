# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHANGELOG.md to track all project changes
- Steering file (system-file-changelog.md) to enforce changelog updates
- Missing test-dev.md prompt file for test-dev agent

### Changed
- Updated Foundation files (product.md, tech.md, structure.md) to v1.1 with complete project details
- Updated project-build.md to v1.4 with configuration files and dependencies
- Updated project-init.md to v1.2 with interface-check specific details
- Simplified hello.py with proper docstring comment

## [0.1.0] - 2026-01-15

### Added
- Initial project structure with src/ organization
- Web-based GUI using NiceGUI 2.24.2
- SSH connection management with multi-hop support
- Interface monitoring tools (ethtool, mlxlink, mlxconfig, mst, rdma)
- SLX switch scanner with eye scan automation
- SUT system monitoring with configurable components
- Iperf traffic testing with bidirectional support
- Real-time data visualization with Plotly
- CSV logging and log analysis tools
- Pydantic configuration models
- Custom Kiro agents for specialized workflows

### Infrastructure
- UV package manager setup
- Ruff linter/formatter configuration (line-length: 120)
- MyPy strict type checking
- Pytest with coverage
- PyInstaller binary build support

### Documentation
- README.md with project overview
- Foundation documents (product.md, tech.md, structure.md)
- Agent reference guide
- System file standards (style, hooks, agents, version, header)
- Project build and initialization instructions

[Unreleased]: https://github.com/yourusername/interface-check/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/interface-check/releases/tag/v0.1.0
