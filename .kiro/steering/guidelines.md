---
title: Interface Check - Development Guidelines
inclusion: always
---

# Interface Check - Development Guidelines

This document provides an overview of development guidelines for the Interface Check project. Detailed patterns and practices are organized into focused files:

## Core Development Standards
- **[Code Quality Standards](code-quality-standards.md)** - Type hints, documentation, error handling, and quality tools
- **[Architecture Patterns](architecture-patterns.md)** - Class design, threading, configuration, and data processing patterns
- **[UI Development Patterns](ui-development-patterns.md)** - NiceGUI patterns, user experience, and state management

## Project-Specific Patterns
- **[SSH Connection Patterns](ssh-connection-patterns.md)** - Connection management, multi-hop SSH, and security practices
- **[Threading Patterns](threading-patterns.md)** - Worker threads, queue communication, and synchronization
- **[Network Tools Integration](network-tools-integration.md)** - Tool abstraction, execution patterns, and data processing
- **[Configuration Patterns](configuration-patterns.md)** - Settings management, validation, and security
- **[Traffic Testing Patterns](traffic-testing-patterns.md)** - Iperf management, bandwidth monitoring, and web UI
- **[Data Analysis Patterns](data-analysis-patterns.md)** - CSV processing, statistical analysis, and reporting
- **[Error Handling Patterns](error-handling-patterns.md)** - Exception management, recovery, and user experience

## General Best Practices
- **[Python Best Practices](python-best-practices.md)** - Python-specific coding standards and conventions
- **[Testing Best Practices](testing-best-practices.md)** - Test execution, organization, and CI/CD considerations
- **[Security Best Practices](security-best-practices.md)** - Code security, dependency management, and infrastructure security
- **[Git Best Practices](git-best-practices.md)** - Commit messages, branching, and repository management

## Technology and Tools
- **[Technology Stack](tech.md)** - Programming language, dependencies, and development tools
- **[Development Standards](development-standards.md)** - Dependency management, file organization, and quality assurance
- **[MCP Best Practices](mcp-best-practices.md)** - Model Context Protocol server configuration and usage
- **[Monitoring & Observability](monitoring-observability.md)** - Application monitoring, logging, and alerting
- **[Deployment Patterns](deployment-patterns.md)** - Production deployment, environment management, and service management

## Project Structure
- **[Project Structure](structure.md)** - Directory organization and architectural relationships
- **[Product Overview](product.md)** - Purpose, features, target users, and use cases

## Key Principles

### Code Quality
- Comprehensive type hints for all functions and methods
- Google-style docstrings for all public classes and methods
- Comprehensive error handling with logging integration
- 120 character line length with ruff formatting

### Architecture
- Layered architecture with clear separation of concerns
- Event-driven updates for real-time data visualization
- Queue-based communication for thread safety
- Configuration-driven design for flexibility

### Development Workflow
- Use UV for modern Python package management
- Ruff for comprehensive linting and formatting
- MyPy for strict type checking
- GitHub Actions for automated CI/CD

### Project Standards
- Never create duplicate files with backup suffixes
- Work iteratively on existing files
- Maintain clean directory structures
- Use meaningful variable and function names
- Keep functions small and focused on single responsibilities
