---
title:        DevContainer Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# DevContainer Best Practices

## Overview

Development Containers (DevContainers) provide consistent, portable, and reproducible development environments using Docker containers. This guide covers essential best practices for creating production-ready DevContainer configurations.

## Core Benefits

- **Environment Consistency**: Eliminates "works on my machine" issues across team members
- **Portable Development**: Works identically across Windows, macOS, and Linux
- **Dependency Isolation**: Keeps project dependencies separate from host system
- **Fast Onboarding**: New team members productive in minutes, not hours
- **Automation**: Auto-installs extensions, tools, and dependencies

## Configuration Structure

### Basic File Structure
```
.devcontainer/
├── devcontainer.json          # Main configuration
├── Dockerfile                 # Custom image (optional)
├── docker-compose.yml         # Multi-service setup (optional)
└── .env                      # Environment variables (optional)
```

## Essential Configuration Best Practices

### 1. Use Specific Base Images

**✅ DO:**
```json
{
  "image": "mcr.microsoft.com/devcontainers/javascript-node:18.17.0"
}
```

**❌ DON'T:**
```json
{
  "image": "node:latest"
}
```

### 2. Pin Extension Versions

**✅ DO:**
```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint@2.4.2",
        "esbenp.prettier-vscode@10.1.0"
      ]
    }
  }
}
```

### 3. Configure Port Forwarding Properly

```json
{
  "forwardPorts": [3000, 5432],
  "portsAttributes": {
    "3000": {
      "label": "Application",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "PostgreSQL",
      "onAutoForward": "silent"
    }
  }
}
```

## Security Best Practices

### 1. Run as Non-Root User

```json
{
  "remoteUser": "node",
  "containerUser": "node"
}
```

### 2. Use Specific Image Tags

Avoid `latest` tags to ensure reproducible builds:
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.11.5-bullseye"
}
```

### 3. Mount SSH Keys Securely

```json
{
  "mounts": [
    "source=${localEnv:HOME}/.ssh,target=/home/node/.ssh,readonly,type=bind"
  ]
}
```

### 4. Environment Variable Management

```json
{
  "containerEnv": {
    "NODE_ENV": "development"
  },
  "runArgs": ["--env-file", ".devcontainer/.env"]
}
```

## Multi-Service Setup with Docker Compose

### docker-compose.yml Example

```yaml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - .:/workspace:cached
      - node_modules:/workspace/node_modules
    command: sleep infinity
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://dev:secret@db:5432/appdb
      REDIS_URL: redis://redis:6379

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

volumes:
  postgres-data:
  redis-data:
  node_modules:
```

### Corresponding devcontainer.json

```json
{
  "name": "Full-stack Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ckolkman.vscode-postgres"
      ]
    }
  },
  "forwardPorts": [3000, 5432, 6379],
  "postCreateCommand": "npm install && npm run db:migrate",
  "remoteUser": "node"
}
```

## Performance Optimization

### 1. Use Named Volumes for Dependencies

```json
{
  "mounts": [
    "source=myproject-node_modules,target=${containerWorkspaceFolder}/node_modules,type=volume"
  ]
}
```

### 2. Optimize File Mounting

```json
{
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached"
}
```

### 3. Leverage Build Cache

```dockerfile
# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy source code after dependencies
COPY . .
```

## Lifecycle Commands

### Command Types and Usage

```json
{
  "postCreateCommand": "npm install",           // Run once after container creation
  "postStartCommand": "npm run dev",            // Run every container start
  "postAttachCommand": "echo 'Container ready'", // Run when VS Code attaches
  "initializeCommand": "echo 'Before container'" // Run on host before container
}
```

### Complex Setup Example

```json
{
  "postCreateCommand": [
    "npm install",
    "npm run build",
    "npm run db:setup"
  ]
}
```

## Custom Dockerfile Best Practices

### Secure Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM node:18.17.0-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Development stage
FROM node:18.17.0-alpine AS development

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["sleep", "infinity"]
```

## Team Collaboration

### 1. Version Control Integration

Always commit `.devcontainer/` folder:
```bash
git add .devcontainer/
git commit -m "Add DevContainer configuration"
```

### 2. Documentation

Include setup instructions in README:
```markdown
## Development Setup

This project uses VS Code Dev Containers:

1. Install Docker Desktop and VS Code
2. Install "Dev Containers" extension
3. Clone repository and open in VS Code
4. Click "Reopen in Container" when prompted
```

### 3. Environment-Specific Configurations

```
.devcontainer/
├── devcontainer.json          # Default (full-stack)
├── frontend/
│   └── devcontainer.json      # Frontend-only
└── backend/
    └── devcontainer.json      # Backend with database
```

## Troubleshooting Common Issues

### Container Won't Start
- Verify Docker is running: `docker --version`
- Check Docker Desktop settings
- Rebuild without cache: "Dev Containers: Rebuild Container Without Cache"

### Slow Performance (macOS/Windows)
- Use named volumes for `node_modules`
- Enable file sharing in Docker Desktop
- Use `cached` mount consistency

### Extensions Not Installing
- Verify extension IDs are correct
- Check extension compatibility with remote containers
- Rebuild container to refresh extensions

### Port Conflicts
- Check for conflicting containers: `docker ps`
- Use different port mappings
- Stop conflicting services

## Advanced Features

### 1. Features Integration

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "18"
    },
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  }
}
```

### 2. Health Checks

```json
{
  "postStartCommand": "curl -f http://localhost:3000/health || exit 1"
}
```

### 3. Resource Limits

```json
{
  "runArgs": [
    "--memory=2g",
    "--cpus=2"
  ]
}
```

## CI/CD Integration

### Use Same Image in CI

```yaml
# GitHub Actions example
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/devcontainers/javascript-node:18
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
```

## Complete Example Configuration

### devcontainer.json (Production-Ready)

```json
{
  "name": "Node.js Development Container",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:18.17.0",
  
  "customizations": {
    "vscode": {
      "settings": {
        "terminal.integrated.defaultProfile.linux": "bash",
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "eslint.validate": ["javascript", "typescript"]
      },
      "extensions": [
        "dbaeumer.vscode-eslint@2.4.2",
        "esbenp.prettier-vscode@10.1.0",
        "eamodio.gitlens@14.3.0",
        "ms-azuretools.vscode-docker@1.26.0"
      ]
    }
  },
  
  "forwardPorts": [3000, 5432],
  "portsAttributes": {
    "3000": {
      "label": "Application",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "Database",
      "onAutoForward": "silent"
    }
  },
  
  "postCreateCommand": "npm install && npm run setup",
  "postStartCommand": "npm run dev",
  
  "containerEnv": {
    "NODE_ENV": "development",
    "PORT": "3000"
  },
  
  "remoteUser": "node",
  
  "mounts": [
    "source=${localEnv:HOME}/.ssh,target=/home/node/.ssh,readonly,type=bind",
    "source=myproject-node_modules,target=${containerWorkspaceFolder}/node_modules,type=volume"
  ],
  
  "runArgs": [
    "--env-file", ".devcontainer/.env"
  ]
}
```

## Key Takeaways

1. **Always use specific image versions** - avoid `latest` tags
2. **Run as non-root user** - essential for security
3. **Pin extension versions** - ensures consistent tooling
4. **Use named volumes** - improves performance for dependencies
5. **Commit configuration to version control** - enables team consistency
6. **Document setup process** - helps new team members
7. **Test configurations regularly** - ensure they work across environments
8. **Use multi-stage builds** - optimize for both development and production
9. **Implement proper signal handling** - use dumb-init or tini
10. **Monitor resource usage** - set appropriate limits

## Resources

- [Official DevContainers Documentation](https://containers.dev/)
- [Microsoft DevContainer Images](https://github.com/devcontainers/images)
- [DevContainer Features](https://containers.dev/features)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)

## Version History

- v1.0 (2026-01-12): Initial version based on comprehensive research of current best practices

---

*Content was rephrased for compliance with licensing restrictions*
