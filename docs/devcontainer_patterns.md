---
title:        Devcontainer Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Devcontainer Patterns

## Core Principles

1. **Reproducibility First** - Devcontainers solve "works on my machine" by containerizing the entire development environment with consistent toolchains, dependencies, and configurations.

2. **Isolation by Design** - The container has its own filesystem, network stack, and process tree. Code running inside cannot access host files unless explicitly mounted.

3. **Configuration as Code** - All environment setup lives in version-controlled `devcontainer.json` and associated Dockerfiles, enabling fast onboarding and consistent environments across teams.

4. **Minimal Base Images** - Start with the smallest viable base image and add only what's needed. Reduces attack surface and build times.

5. **Secrets Never in Images** - Credentials, tokens, and sensitive configuration must never be baked into images or committed to version control.

## Essential Patterns

### Configuration Approaches (Choose One)

| Approach | Use Case | Complexity |
|----------|----------|------------|
| **Image-only** | Simple projects, standard toolchains | Low |
| **Dockerfile** | Custom dependencies, build steps | Medium |
| **Docker Compose** | Multi-service (app + database + cache) | High |

### Lifecycle Scripts (Execution Order)

```
initializeCommand     → Host, before container creation
onCreateCommand       → Container, first creation only
updateContentCommand  → Container, after content update
postCreateCommand     → Container, after creation
postStartCommand      → Container, every start
postAttachCommand     → Container, every attach
```

**Best Practice**: Use `initializeCommand` for host-side secret injection, `postCreateCommand` for dependency installation, `postStartCommand` for cleanup.

### Features for Common Tools

Use devcontainer features instead of custom Dockerfile instructions for standard tooling:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  }
}
```

Features are predefined scripts that extend base images without custom Dockerfiles.

### Multi-Service with Docker Compose

```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "shutdownAction": "stopCompose"
}
```

Use for projects requiring databases, caches, or message queues alongside the development container.

### Non-Root User Configuration

```json
{
  "remoteUser": "vscode",
  "containerUser": "vscode"
}
```

Always run as non-root inside containers. Most base images create a `vscode` user by default.

## Anti-Patterns to Avoid

### 1. Storing Secrets in Images or Environment Files

**Wrong:**
```json
{
  "containerEnv": {
    "API_KEY": "sk-1234567890abcdef"
  }
}
```

**Right:** Use secret managers (1Password, Vault) with just-in-time injection:
```json
{
  "initializeCommand": "op read 'op://Vault/Item/field' > .env.local",
  "postStartCommand": "rm -f .env.local"
}
```

### 2. Running Multiple Services in One Container

**Wrong:** Web server + database + cache in single container.

**Right:** Use Docker Compose with separate services. Each container should have one responsibility.

### 3. Applying Updates Inside Running Containers

**Wrong:** Running `apt upgrade` inside containers.

**Right:** Rebuild images with updated base images. Containers should be immutable and reproducible.

### 4. Hardcoded Configuration

**Wrong:** Baking environment-specific settings into Dockerfiles.

**Right:** Use environment variables, mounted config files, or secret references:
```json
{
  "runArgs": ["--env-file", "${localWorkspaceFolder}/.env.development"]
}
```

### 5. Privileged Containers Without Justification

**Wrong:**
```json
{
  "runArgs": ["--privileged"]
}
```

**Right:** Use specific capabilities only when required:
```json
{
  "capAdd": ["SYS_PTRACE"],
  "securityOpt": ["seccomp=unconfined"]
}
```

### 6. Large Monolithic Images

**Wrong:** Single Dockerfile with all build tools, runtime, and dev dependencies.

**Right:** Multi-stage builds separating build and runtime:
```dockerfile
FROM node:22 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22-slim
COPY --from=builder /app/node_modules ./node_modules
```

### 7. Treating Containers Like VMs

**Wrong:** SSH into containers, manual configuration, persistent state.

**Right:** Declarative configuration, ephemeral containers, external state storage.

## Implementation Guidelines

### Minimal devcontainer.json Template

```json
{
  "name": "Project Dev",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "charliermarsh.ruff"],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      }
    }
  },
  "postCreateCommand": "pip install -e '.[dev]'",
  "remoteUser": "vscode"
}
```

### Docker Compose Multi-Service Template

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - .:/workspace:cached
    command: sleep infinity
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: devpassword
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres-data:
```

### Secret Injection Pattern (1Password Example)

```json
{
  "initializeCommand": [
    "bash", "-c",
    "op read 'op://Dev/API_TOKEN/credential' > ${localWorkspaceFolder}/.env.secrets"
  ],
  "runArgs": [
    "--env-file", "${localWorkspaceFolder}/.env.secrets"
  ],
  "postStartCommand": "rm -f .env.secrets"
}
```

### Port Forwarding vs Publishing

- **forwardPorts**: Exposes container ports to host (development)
- **appPort**: Publishes ports (production-like, use sparingly)

```json
{
  "forwardPorts": [3000, 5432],
  "portsAttributes": {
    "3000": {"label": "App", "onAutoForward": "notify"},
    "5432": {"label": "Database", "onAutoForward": "silent"}
  }
}
```

### Host Requirements (Optional)

```json
{
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  }
}
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Container build time | < 2 minutes | CI pipeline timing |
| Image size | < 1GB | `docker images` |
| Onboarding time | < 15 minutes | New developer setup |
| Environment parity | 100% | No "works on my machine" issues |
| Secret exposure | 0 incidents | Security audit |
| Container startup | < 30 seconds | `postStartCommand` completion |

## Sources & References

[containers.dev JSON Reference](https://containers.dev/implementors/json_reference/) — Official devcontainer.json specification with all properties, lifecycle scripts, and variable substitution syntax accessed 2025-01-13

[How-To Geek: 7 Docker Anti-Patterns](https://www.howtogeek.com/devops/7-docker-anti-patterns-you-need-to-avoid/) — Comprehensive coverage of ephemeral filesystems, single-process containers, hardcoded secrets, and image build side effects accessed 2025-01-13

[Node.js Security: DevContainers and 1Password](https://www.nodejs-security.com/blog/mitigate-supply-chain-security-with-devcontainers-and-1password-for-nodejs-local-development) — Detailed guide on secret injection patterns, 1Password Connect integration, and supply chain security mitigation accessed 2025-01-13

[Wiz: Docker Secrets Guide](https://www.wiz.io/academy/container-security/docker-secrets) — Security risks of environment variables and build arguments, proper secrets management approaches accessed 2025-01-13

[Pamela Fox: Multi-Service Dev Containers](https://blog.pamelafox.org/2024/11/making-dev-container-with-multiple-data.html) — Patterns for Docker Compose integration with multiple data services accessed 2025-01-13

[Some Natalie: Securing Multi-Service Devcontainers](https://some-natalie.dev/blog/multiservice-devcontainers/) — Security considerations for Docker Compose devcontainer configurations accessed 2025-01-13

## Version History

- v1.0 (2025-01-13 00:00:00): Initial version with core principles, patterns, anti-patterns, and implementation guidelines
