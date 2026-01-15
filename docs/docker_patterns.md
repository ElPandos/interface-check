---
title:        Docker Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Docker Patterns

## Core Principles

1. **Immutability**: Treat containers as immutable artifacts—never modify running containers; rebuild and redeploy instead.

2. **Minimal Attack Surface**: Use minimal base images (Alpine, distroless), run as non-root, and include only runtime dependencies.

3. **Layer Efficiency**: Optimize Dockerfile instruction order for cache utilization; place frequently changing instructions last.

4. **Configuration Externalization**: Never bake secrets or environment-specific config into images; inject at runtime via env vars, secrets, or config maps.

5. **Single Responsibility**: One process per container; compose multiple containers for complex applications.

## Essential Patterns

### Multi-Stage Builds
Separate build and runtime environments to minimize final image size:

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER node
CMD ["node", "dist/main.js"]
```

### Layer Caching Optimization
Order instructions from least to most frequently changing:

```dockerfile
FROM python:3.12-slim

# System deps (rarely change)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (changes frequently)
COPY . .
```

### Non-Root User Pattern
Always run containers as non-root:

```dockerfile
FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/app
COPY --chown=appuser:appuser . .

USER appuser
CMD ["python", "main.py"]
```

### Health Checks
Enable container orchestration to detect unhealthy services:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

### .dockerignore Pattern
Exclude unnecessary files to reduce build context and protect secrets:

```
.git
.gitignore
.env
.env.*
__pycache__
*.pyc
node_modules
.pytest_cache
.coverage
*.log
Dockerfile*
docker-compose*
.dockerignore
README.md
docs/
tests/
```

### Pinned Base Images
Always use specific version tags, never `latest`:

```dockerfile
# Good
FROM python:3.12.1-slim-bookworm

# Bad
FROM python:latest
```

## Anti-Patterns to Avoid

### 1. Running as Root
**Problem**: Container compromise leads to host compromise.
**Fix**: Always use `USER` instruction with non-root user.

### 2. Using `latest` Tag
**Problem**: Non-reproducible builds; unexpected breaking changes.
**Fix**: Pin specific version tags (e.g., `python:3.12.1-slim`).

### 3. Storing Secrets in Images
**Problem**: Secrets exposed in image layers, even if deleted later.
**Fix**: Use Docker secrets, environment variables at runtime, or secret management tools.

### 4. Fat Images with Build Tools
**Problem**: Large attack surface, slow deployments, wasted resources.
**Fix**: Multi-stage builds; copy only runtime artifacts.

### 5. Ignoring .dockerignore
**Problem**: Bloated build context, leaked secrets, slow builds.
**Fix**: Always maintain comprehensive `.dockerignore`.

### 6. One Layer Per RUN
**Problem**: Excessive layers, larger images, slower pulls.
**Fix**: Chain related commands with `&&`:

```dockerfile
# Bad
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# Good
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

### 7. Building Different Images Per Environment
**Problem**: "Works on my machine" issues; untested production images.
**Fix**: Build once, configure at runtime via environment variables.

### 8. No Health Checks
**Problem**: Orchestrators cannot detect unhealthy containers.
**Fix**: Always define `HEALTHCHECK` in Dockerfile or compose.

### 9. Mixing Build and Runtime in Same Stage
**Problem**: Bloated images with compilers, SDKs, dev dependencies.
**Fix**: Multi-stage builds with minimal runtime base.

### 10. Hardcoded Configuration
**Problem**: Inflexible images requiring rebuilds for config changes.
**Fix**: Use environment variables, config files mounted at runtime.

## Implementation Guidelines

### Step 1: Choose Minimal Base Image
- Alpine Linux for most use cases (~5MB)
- Distroless for maximum security (no shell)
- Language-specific slim variants (e.g., `python:3.12-slim`)

### Step 2: Structure Dockerfile for Caching
1. Base image and system packages
2. Create non-root user
3. Copy dependency manifests (package.json, requirements.txt)
4. Install dependencies
5. Copy application code
6. Set user and entrypoint

### Step 3: Implement Security Controls
- Run as non-root user
- Use read-only filesystem where possible
- Drop all capabilities, add only required ones
- Scan images for vulnerabilities (Trivy, Snyk)

### Step 4: Configure Health Monitoring
```yaml
# docker-compose.yml
services:
  app:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

### Step 5: Externalize Configuration
```yaml
services:
  app:
    build: .
    environment:
      - DATABASE_URL
      - LOG_LEVEL=info
    secrets:
      - db_password
```

### Step 6: Integrate into CI/CD
- Build images in CI pipeline
- Tag with git SHA and semantic version
- Scan for vulnerabilities before push
- Push to registry only on successful tests

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Image Size | <100MB for apps, <500MB for ML | `docker images` |
| Build Time | <2 min with cache | CI pipeline duration |
| Vulnerability Count | 0 critical, 0 high | Trivy/Snyk scan |
| Layer Count | <15 layers | `docker history` |
| Non-Root Compliance | 100% | Audit `USER` instruction |
| Health Check Coverage | 100% | Audit compose/k8s configs |
| Secret Exposure | 0 | Image layer inspection |
| Cache Hit Rate | >80% | CI build logs |

## Sources & References

- [Codefresh - Docker Anti Patterns](https://codefresh.io/containers/docker-anti-patterns) — Comprehensive anti-pattern catalog
- [Modern Docker Best Practices 2025](https://talent500.com/blog/modern-docker-best-practices-2025/) — Updated practices including compose v2
- [Docker Layers, Caching & Multi-Stage Builds](https://atharvaunde.com/blogs/docker-layers-caching-multi-stage-explained) — Layer optimization techniques
- [Docker Secrets Guide](https://www.wiz.io/academy/container-security/docker-secrets) — Secure secrets management
- [Dockerfile Best Practices Repository](https://github.com/dnaprawa/dockerfile-best-practices) — Production-ready patterns
- [Faster CI Builds with Docker Cache](https://testdriven.io/blog/faster-ci-builds-with-docker-cache/) — BuildKit caching strategies
- [Docker Privileges and Permissions](https://blog-old.poespas.me/posts/2024/05/24/docker-privileges-and-permissions/) — Security deep dive

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
