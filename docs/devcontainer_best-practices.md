---
title:        Dev Container Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Dev Container Best Practices

## Core Principles

1. **Reproducibility First**: Dev containers must produce identical environments across machines, eliminating "works on my machine" issues through declarative configuration.

2. **Separation of Concerns**: Keep development containers distinct from production images—dev containers include tooling, debugging capabilities, and developer conveniences that don't belong in production.

3. **Minimal Base, Composable Features**: Start with minimal base images and layer functionality through official Features rather than monolithic custom Dockerfiles.

4. **Configuration as Code**: All environment configuration lives in version-controlled `devcontainer.json` and associated files, enabling team-wide consistency.

5. **Security by Default**: Run as non-root user (`remoteUser`), avoid `privileged` mode unless absolutely necessary, and never embed secrets in configuration.

## Essential Practices

### Container Configuration

```json
{
  "name": "project-dev",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "remoteUser": "vscode",
  "containerUser": "vscode",
  "updateRemoteUserUID": true,
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.12"
    },
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"],
      "settings": {"python.defaultInterpreterPath": "/usr/local/bin/python"}
    }
  }
}
```

### Lifecycle Scripts (Execution Order)

| Script | Runs | Use Case |
|--------|------|----------|
| `initializeCommand` | Host machine, before container | Clone submodules, validate prerequisites |
| `onCreateCommand` | Container, first creation only | Install dependencies, compile assets |
| `updateContentCommand` | Container, on content changes | Refresh dependencies after git pull |
| `postCreateCommand` | Container, after user assignment | User-specific setup, secrets access |
| `postStartCommand` | Container, every start | Start background services |
| `postAttachCommand` | Container, every attach | Shell customization, status display |

### Environment Variables

```json
{
  "containerEnv": {
    "PYTHONDONTWRITEBYTECODE": "1",
    "APP_ENV": "development"
  },
  "remoteEnv": {
    "PATH": "${containerEnv:PATH}:/workspace/.venv/bin",
    "AWS_PROFILE": "${localEnv:AWS_PROFILE}"
  }
}
```

- Use `containerEnv` for static values (requires rebuild to change)
- Use `remoteEnv` for dynamic values and path modifications
- Reference host variables with `${localEnv:VAR_NAME}`

### Features (Official Registry)

Prefer official features from `ghcr.io/devcontainers/features/`:

- `common-utils` - Base utilities, non-root user setup
- `python`, `node`, `go`, `rust` - Language runtimes
- `docker-in-docker` or `docker-outside-of-docker` - Container tooling
- `git`, `github-cli`, `aws-cli` - Development tools

### Port Forwarding

```json
{
  "forwardPorts": [8000, 5432],
  "portsAttributes": {
    "8000": {"label": "App", "onAutoForward": "notify"},
    "5432": {"label": "Database", "onAutoForward": "silent"}
  },
  "otherPortsAttributes": {"onAutoForward": "ignore"}
}
```

## Anti-Patterns to Avoid

### Configuration Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Running as root | Security risk, permission issues on bind mounts | Set `remoteUser` to non-root user |
| Hardcoded secrets | Secrets in version control | Use `${localEnv:SECRET}` or secrets management |
| Monolithic Dockerfile | Hard to maintain, slow rebuilds | Use Features for composable tooling |
| Environment-specific images | Different images per env | Single image + environment variables |
| Missing `updateRemoteUserUID` | UID mismatch on Linux hosts | Enable `updateRemoteUserUID: true` |

### Lifecycle Script Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Heavy `postStartCommand` | Slow container starts | Move to `onCreateCommand` |
| Network calls in `initializeCommand` | Runs on host, may fail in CI | Move to container lifecycle scripts |
| No error handling | Silent failures | Use `set -e` in scripts, check exit codes |
| Blocking `postAttachCommand` | Delays terminal availability | Use background processes or `postStartCommand` |

### Docker Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `privileged: true` without need | Full host access, security risk | Use specific `capAdd` capabilities |
| Unbounded volume mounts | Performance issues, security | Mount only required directories |
| Missing `.dockerignore` | Large build context, slow builds | Exclude `node_modules`, `.git`, build artifacts |
| `latest` tag for base images | Non-reproducible builds | Pin specific versions |

## Implementation Guidelines

### Project Structure

```
.devcontainer/
├── devcontainer.json      # Main configuration
├── Dockerfile             # Optional custom image
├── docker-compose.yml     # Optional multi-container
└── scripts/
    ├── post-create.sh     # Setup script
    └── post-start.sh      # Startup script
```

### Multi-Container Setup (Docker Compose)

```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "shutdownAction": "stopCompose",
  "runServices": ["app", "db"]
}
```

### Performance Optimization

1. **Use named volumes for dependencies**:
   ```json
   {
     "mounts": [
       {"source": "node_modules", "target": "/workspace/node_modules", "type": "volume"}
     ]
   }
   ```

2. **Enable BuildKit caching**:
   ```json
   {
     "build": {
       "dockerfile": "Dockerfile",
       "cacheFrom": "ghcr.io/org/project-devcontainer:cache"
     }
   }
   ```

3. **Prebuild for CI/Codespaces**:
   - Use `onCreateCommand` and `updateContentCommand` for cacheable operations
   - Reserve `postCreateCommand` for user-specific setup

### Security Configuration

```json
{
  "remoteUser": "vscode",
  "containerUser": "vscode",
  "updateRemoteUserUID": true,
  "capAdd": ["SYS_PTRACE"],
  "securityOpt": ["seccomp=unconfined"],
  "privileged": false
}
```

- `SYS_PTRACE` enables debugging (C++, Go, Rust)
- `seccomp=unconfined` may be needed for some debuggers
- Avoid `privileged` unless Docker-in-Docker is required

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Container build time | < 5 min (cold), < 30s (cached) | CI pipeline timing |
| Environment setup time | < 2 min from clone to coding | Manual testing |
| Configuration drift | 0 differences across team | Periodic audits |
| Security findings | 0 critical/high in container scan | Trivy/Snyk scans |
| Feature adoption | 100% team using devcontainer | Usage analytics |

### Validation Checklist

- [ ] Container builds successfully from clean state
- [ ] All lifecycle scripts complete without errors
- [ ] Non-root user can perform all development tasks
- [ ] Port forwarding works for all required services
- [ ] Extensions install and configure correctly
- [ ] Environment variables resolve properly
- [ ] Volume mounts have correct permissions

## Sources & References

- [Dev Container Specification](https://containers.dev/implementors/spec/) — Official specification
- [devcontainer.json Reference](https://containers.dev/implementors/json_reference/) — Complete property reference
- [Official Features Registry](https://containers.dev/features) — Maintained feature collection
- [devcontainers/features](https://github.com/devcontainers/features) — Feature source code
- [Docker Anti-Patterns](https://codefresh.io/blog/docker-anti-patterns/) — Container best practices

## Version History

- v1.0 (2025-01-13 00:00:00): Initial version based on Dev Container Specification and community best practices
