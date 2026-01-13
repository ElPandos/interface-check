# Research Output – 2026-01-13 00:38 CET

## Original Prompt
> Research best docker practices. Use the research file to create/update .kiro/steering/docker_best-practices.md

## Complete Response

Based on comprehensive research of current Docker best practices for 2025, here are the essential practices for building secure, efficient, and production-ready Docker containers:

## Core Security Practices

### 1. Multi-Stage Builds for Security
Multi-stage builds are fundamental for production security, reducing attack surface by 30-70% by excluding build tools and dependencies from final images:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Production stage with minimal footprint
FROM node:18-alpine AS production
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --chown=nextjs:nodejs . .
USER nextjs
```

### 2. Distroless and Minimal Base Images
Google's distroless images contain only application and runtime dependencies, eliminating shells and package managers that could be exploited:

```dockerfile
FROM gcr.io/distroless/java:11
COPY --from=builder /app/target/app.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### 3. Non-Root User Execution
Always run containers as non-root users to limit potential damage from container escapes:

```dockerfile
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup
USER appuser
```

### 4. Vulnerability Scanning Integration
Implement automated vulnerability scanning in CI/CD pipelines:

```bash
# Using Trivy for comprehensive scanning
trivy image --severity HIGH,CRITICAL myapp:latest
```

## Performance Optimization

### 1. Layer Caching Strategy
Structure Dockerfiles to maximize cache hits, achieving up to 70% faster builds:

```dockerfile
# Dependencies first (changes less frequently)
COPY package*.json ./
RUN npm ci --only=production

# Source code last (changes frequently)
COPY . .
RUN npm run build
```

### 2. Build Context Optimization
Use comprehensive .dockerignore files to minimize build context:

```dockerignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.cache
dist
build
*.md
.DS_Store
```

### 3. BuildKit Utilization
Enable BuildKit for advanced caching and parallel builds:

```bash
export DOCKER_BUILDKIT=1
docker build --cache-from myapp:cache .
```

## Production Deployment Practices

### 1. Health Checks Implementation
Implement comprehensive health checks covering application, database, and network status:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 2. Signal Handling
Use proper init systems for signal handling:

```dockerfile
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

### 3. Resource Limits
Set appropriate resource constraints:

```yaml
# Docker Compose example
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## CI/CD Integration

### 1. Automated Security Scanning
Block deployments with critical vulnerabilities:

```yaml
# GitHub Actions example
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myapp:${{ github.sha }}'
    format: 'sarif'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
```

### 2. Image Versioning Strategy
Use semantic versioning and immutable tags:

```bash
docker build -t myapp:1.2.3 -t myapp:latest .
docker push myapp:1.2.3
```

### 3. Multi-Architecture Builds
Support multiple architectures for broader deployment:

```yaml
- name: Build and push multi-arch
  uses: docker/build-push-action@v4
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: myapp:latest
```

## Container Hardening

### 1. Capability Dropping
Remove unnecessary Linux capabilities:

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```

### 2. Read-Only Root Filesystem
Mount root filesystem as read-only:

```bash
docker run --read-only --tmpfs /tmp myapp
```

### 3. Security Profiles
Use AppArmor or SELinux profiles for additional security:

```bash
docker run --security-opt apparmor:docker-default myapp
```

## Monitoring and Observability

### 1. Structured Logging
Implement structured logging for better observability:

```dockerfile
ENV LOG_LEVEL=info
ENV LOG_FORMAT=json
```

### 2. Metrics Exposure
Expose application metrics for monitoring:

```dockerfile
EXPOSE 8080 9090
# 8080 for application, 9090 for metrics
```

### 3. Container Health Monitoring
Implement comprehensive container health monitoring with automated alerts for production environments.

## Key Findings

- **Multi-stage builds** are essential for security, reducing attack surface by excluding build tools from production images
- **Distroless images** eliminate common attack vectors by removing shells and package managers
- **Layer caching optimization** can achieve up to 70% faster build times through strategic Dockerfile structuring
- **Vulnerability scanning integration** in CI/CD pipelines is now standard practice for production deployments
- **Non-root user execution** is critical for container security and should be implemented in all production containers

## Sources & References

- [Multi Stage Docker Build Tutorial](https://www.restack.io/p/open-source-ai-projects-answer-multi-stage-docker-build-cat-ai) — Multi-stage build security benefits, accessed 2026-01-13
- [10 Docker Security Best Practices](https://snyksec.hashnode.dev/10-docker-image-security-best-practices) — Security practices including distroless images, accessed 2026-01-13
- [Mastering Docker Best Practices for 2025](https://www.nerdleveltech.com/mastering-docker-best-practices-for-2025) — Production deployment practices, accessed 2026-01-13
- [70% Faster Builds with Layer Caching](https://www.devopsroles.com/boost-docker-build-speed-with-layer-caching/) — Performance optimization techniques, accessed 2026-01-13
- [Docker Production Optimization](https://fenilsonani.com/articles/docker-production-optimization-security) — Enterprise security and performance practices, accessed 2026-01-13

## Tools & Methods Used

- web_search: "Docker best practices 2025 security multi-stage builds production deployment"
- web_search: "Docker security best practices 2025 vulnerability scanning distroless images rootless containers"
- web_search: "Docker production deployment best practices 2025 health checks monitoring CI/CD"
- web_search: "Docker performance optimization 2025 layer caching build context .dockerignore"

## Metadata

- Generated: 2026-01-13T00:38:22+01:00
- Model: Claude 3.5 Sonnet
- Tags: docker, containers, security, performance, production, ci-cd
- Confidence: High - based on current industry practices and recent documentation
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Practices may evolve with new Docker releases and security discoveries
- Implementation should be tested in specific environments before production deployment
- Some advanced features may require Docker Engine 20.10+ or specific orchestration platforms
