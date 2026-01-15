---
title:        Docker Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Docker Best Practices

## Core Principles

1. **Immutability & Statelessness**: Treat containers as disposable units. Externalize state to volumes/databases, configuration to environment variables. Never modify running containers.

2. **Minimal Attack Surface**: Use smallest viable base images (alpine, distroless, slim variants). Include only runtime dependencies. Remove build tools from production images.

3. **Reproducibility**: Pin all image versions to specific tags or SHA256 digests. Never use `:latest` in production. Ensure builds are deterministic.

4. **Least Privilege**: Run containers as non-root users. Drop all capabilities, add back only what's needed. Use read-only filesystems where possible.

5. **Defense in Depth**: Layer security controls—image scanning, runtime protection, network isolation, secrets management. No single point of failure.

## Essential Practices

### Image Optimization

**Multi-stage builds** — Separate build and runtime environments:
```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# Runtime stage
FROM python:3.12-slim
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages
COPY --chown=appuser:appuser src/ /app/
USER appuser
```

**Layer caching** — Order instructions from least to most frequently changed:
```dockerfile
# Dependencies first (changes rarely)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code last (changes often)
COPY . .
```

**Minimize layers** — Combine related commands:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

### Security Hardening

**Non-root user**:
```dockerfile
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser
USER appuser
```

**Drop capabilities**:
```yaml
# docker-compose.yml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed
    read_only: true
    security_opt:
      - no-new-privileges:true
```

**Secrets management** — Never bake secrets into images:
```dockerfile
# BAD: ENV API_KEY=secret123
# GOOD: Pass at runtime
ENV API_KEY=""
```

Use Docker secrets, external vaults, or runtime injection.

### Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

For non-HTTP services:
```dockerfile
HEALTHCHECK CMD pg_isready -U postgres || exit 1
```

### .dockerignore

Essential exclusions:
```
.git
.gitignore
.env*
*.log
*.md
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
node_modules
.venv
Dockerfile*
docker-compose*
```

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Logging

```yaml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

Application should log to stdout/stderr:
```dockerfile
CMD ["python", "-u", "app.py"]  # -u for unbuffered output
```

### Signal Handling

Use exec form for proper signal propagation:
```dockerfile
# GOOD: exec form
ENTRYPOINT ["python", "app.py"]

# BAD: shell form (signals go to shell, not app)
ENTRYPOINT python app.py
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Using `:latest` tag | Non-reproducible builds | Pin to specific version or digest |
| Running as root | Security vulnerability | Create and use non-root user |
| Storing secrets in image | Credential exposure | Use runtime injection/secrets |
| No `.dockerignore` | Bloated context, cache invalidation | Maintain comprehensive ignore file |
| Single-stage builds | Large images with build tools | Use multi-stage builds |
| No health checks | Silent failures, bad orchestration | Define HEALTHCHECK |
| Hardcoded configuration | Inflexible deployments | Use environment variables |
| No resource limits | Resource exhaustion, noisy neighbors | Set CPU/memory limits |
| Installing unnecessary packages | Larger attack surface | Use `--no-install-recommends` |
| Not cleaning apt cache | Wasted space | `rm -rf /var/lib/apt/lists/*` |

## Implementation Guidelines

### Step 1: Base Image Selection
```dockerfile
# Prefer official, minimal images
FROM python:3.12-slim          # Good: official, slim
FROM python:3.12-alpine        # Better: smaller, but glibc issues
FROM gcr.io/distroless/python3 # Best: minimal, no shell
```

### Step 2: Dependency Installation
```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### Step 3: Application Setup
```dockerfile
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8080
```

### Step 4: Runtime Configuration
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "main:app"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
```

### Step 5: Validation
```bash
# Lint Dockerfile
hadolint Dockerfile

# Scan for vulnerabilities
docker scout cves myimage:tag
trivy image myimage:tag

# Validate compose
docker compose config
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Image size | <100MB for apps, <500MB for ML | `docker images` |
| Build time | <2min incremental, <10min clean | CI pipeline metrics |
| Vulnerability count | 0 critical, <5 high | `trivy`/`docker scout` |
| Startup time | <30s to healthy | Health check timing |
| Layer count | <15 layers | `docker history` |
| Non-root execution | 100% of containers | Security audit |
| Resource utilization | <80% of limits | Container metrics |
| Health check pass rate | >99.9% | Orchestrator metrics |

## Sources & References

- [Mastering Docker Best Practices for 2025](https://www.nerdleveltech.com/mastering-docker-best-practices-for-2025) — Comprehensive 2025 practices guide accessed 2026-01-14
- [NEW Docker 2025: 42 Prod Best Practices](https://docs.benchhub.co/docs/tutorials/docker/docker-best-practices-2025) — 42 production practices with examples accessed 2026-01-14
- [10 Essential Docker Best Practices for 2025](https://signiance.com/docker-best-practices/) — Multi-stage builds and security focus accessed 2026-01-14
- [Enterprise-Grade Docker: Production Hardening](https://devopsservices.io/blog/docker-best-practices) — Version pinning and security patches accessed 2026-01-14
- [Dockerfile Best Practices Part 2: Advanced Security](https://www.owais.io/blog/2025-10-03_dockerfile-best-practices-security-production) — 30% smaller images, Trivy scanning accessed 2026-01-14
- [Best Practices for Building Docker Images](https://betterstack.com/community/guides/scaling-docker/docker-build-best-practices/) — Multi-stage builds and optimization accessed 2026-01-14
- [How to Secure Docker Containers](https://www.kdnuggets.com/how-to-secure-docker-containers-with-best-practices) — Alpine images, security hardening accessed 2026-01-14
- [Docker Build Optimization with Layer Caching](https://depot.dev/blog/faster-builds-with-docker-caching) — Cache strategies and optimization accessed 2026-01-14

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
