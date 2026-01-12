# Research Output – 2026-01-12 13:49 CET

## Original Prompt
> Can you research devcontainer best practices? and use the research file to create a .kiro/steering/devcontainer-best-practices.md file

## Complete Response

Based on comprehensive research of current DevContainer best practices from official Microsoft documentation, security experts, and community resources, here are the key findings for 2024-2026:

### Core DevContainer Benefits
- **Environment Consistency**: Eliminates "works on my machine" issues across team members
- **Portable Development**: Works identically across Windows, macOS, and Linux
- **Dependency Isolation**: Keeps project dependencies separate from host system
- **Fast Onboarding**: New team members productive in minutes, not hours
- **Automation**: Auto-installs extensions, tools, and dependencies

### Essential Configuration Best Practices

#### 1. Use Specific Base Images
Always use specific versions rather than `latest` tags for reproducible builds:
```json
{
  "image": "mcr.microsoft.com/devcontainers/javascript-node:18.17.0"
}
```

#### 2. Pin Extension Versions
Specify exact extension versions to ensure consistency:
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

#### 3. Configure Port Forwarding Properly
Use descriptive labels and appropriate auto-forward settings:
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

### Security Best Practices

#### 1. Run as Non-Root User
Critical security practice to follow principle of least privilege:
```json
{
  "remoteUser": "node",
  "containerUser": "node"
}
```

#### 2. Use Specific Image Tags
Avoid `latest` tags to ensure reproducible builds:
```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.11.5-bullseye"
}
```

#### 3. Mount SSH Keys Securely
Use read-only mounts for sensitive data:
```json
{
  "mounts": [
    "source=${localEnv:HOME}/.ssh,target=/home/node/.ssh,readonly,type=bind"
  ]
}
```

#### 4. Environment Variable Management
Use secure methods for environment variables:
```json
{
  "containerEnv": {
    "NODE_ENV": "development"
  },
  "runArgs": ["--env-file", ".devcontainer/.env"]
}
```

### Multi-Service Setup with Docker Compose

For complex applications requiring databases, Redis, etc., use Docker Compose:

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

### Performance Optimization

#### 1. Use Named Volumes for Dependencies
Improves performance, especially on Windows/macOS:
```json
{
  "mounts": [
    "source=myproject-node_modules,target=${containerWorkspaceFolder}/node_modules,type=volume"
  ]
}
```

#### 2. Optimize File Mounting
Use cached consistency for better performance:
```json
{
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached"
}
```

#### 3. Leverage Build Cache
Structure Dockerfile for optimal caching:
```dockerfile
# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy source code after dependencies
COPY . .
```

### Lifecycle Commands

Configure commands for different container lifecycle stages:
```json
{
  "postCreateCommand": "npm install",           // Run once after container creation
  "postStartCommand": "npm run dev",            // Run every container start
  "postAttachCommand": "echo 'Container ready'", // Run when VS Code attaches
  "initializeCommand": "echo 'Before container'" // Run on host before container
}
```

### Custom Dockerfile Best Practices

Use multi-stage builds for security and efficiency:
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

### Team Collaboration

#### 1. Version Control Integration
Always commit `.devcontainer/` folder:
```bash
git add .devcontainer/
git commit -m "Add DevContainer configuration"
```

#### 2. Documentation
Include setup instructions in README:
```markdown
## Development Setup

This project uses VS Code Dev Containers:

1. Install Docker Desktop and VS Code
2. Install "Dev Containers" extension
3. Clone repository and open in VS Code
4. Click "Reopen in Container" when prompted
```

#### 3. Environment-Specific Configurations
```
.devcontainer/
├── devcontainer.json          # Default (full-stack)
├── frontend/
│   └── devcontainer.json      # Frontend-only
└── backend/
    └── devcontainer.json      # Backend with database
```

### Advanced Features

#### 1. Features Integration
Use DevContainer Features for additional tooling:
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

#### 2. Health Checks
Implement container health monitoring:
```json
{
  "postStartCommand": "curl -f http://localhost:3000/health || exit 1"
}
```

#### 3. Resource Limits
Set appropriate resource constraints:
```json
{
  "runArgs": [
    "--memory=2g",
    "--cpus=2"
  ]
}
```

### Common Anti-Patterns to Avoid

1. **Image Building Issues**
   - Using `latest` tags in production
   - Not using multi-stage builds for compiled applications
   - Including build tools in production images
   - Not optimizing layer caching
   - Ignoring .dockerignore files

2. **Security Issues**
   - Running containers as root user
   - Using privileged containers unnecessarily
   - Hardcoding secrets in images
   - Not implementing health checks
   - Exposing unnecessary ports

3. **Resource Management Issues**
   - Not setting resource limits
   - Using inappropriate restart policies
   - Not handling signals properly
   - Ignoring container lifecycle management

## Key Findings

- DevContainers provide consistent, portable development environments using Docker
- Security requires non-root users, specific image versions, and proper secret management
- Performance optimization through named volumes, cached mounts, and multi-stage builds
- Team collaboration enhanced through version control integration and documentation
- Advanced features like DevContainer Features and health checks improve reliability

## Sources & References

- [Developing inside a Container - Visual Studio Code](https://code.visualstudio.com/docs/devcontainers/containers) — Official Microsoft documentation
- [Securing Your Containerised Models And Workloads](https://bytegoblin.io/blog/securing-your-containerised-models-and-workloads) — Security best practices
- [Top 20 Dockerfile best practices](https://sysdig.com/blog/dockerfile-best-practices/) — Dockerfile optimization
- [Running Privileged Docker Containers as Non-Root Users](https://blog.poespas.me/posts/2024/05/22/docker-privileged-containers-for-non-root-users/) — Non-root user configuration
- [Mastering Dev Containers in VS Code](https://www.glukhov.org/post/2025/10/vs-code-dev-containers/) — Comprehensive setup guide

## Tools & Methods Used

- web_search: "DevContainer best practices 2024 2025 security performance configuration"
- web_search: "development containers devcontainer.json best practices VS Code Docker"
- web_search: "DevContainer security best practices non-root user dockerfile optimization 2024"
- web_fetch: https://code.visualstudio.com/docs/devcontainers/containers

## Metadata

- Generated: 2026-01-12T13:49:53+01:00
- Model: Claude 3.5 Sonnet
- Session ID: N/A
- Tool calls total: 4
- Approximate duration: ~5 minutes

## Limitations & Confidence Notes

- Data current as of January 2026 – DevContainer ecosystem evolves rapidly
- Focus on VS Code DevContainers – other IDEs may have different practices
- Security recommendations based on current threat landscape
- Performance optimizations may vary by platform (Windows/macOS/Linux)
- Recommended next steps: Test configurations with specific project requirements and validate security settings
