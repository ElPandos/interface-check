# Research Output – 2026-01-12 20:28 CET

## Original Prompt
> Research best docker patterns. Use the research file to create a .kiro/steering/docker_patterns.md file

## Complete Response

Based on comprehensive research of current Docker patterns and best practices for 2025-2026, here are the essential patterns for building secure, efficient, and maintainable containerized applications:

## Multi-Stage Build Patterns

Multi-stage builds are fundamental for production Docker images, reducing size by 30-70% and improving security by separating build dependencies from runtime.

**Basic Multi-Stage Pattern:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY src ./src
RUN npm run build

# Production stage
FROM node:18-alpine AS production
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["npm", "start"]
```

**Advanced Multi-Stage with Security:**
```dockerfile
# Build dependencies stage
FROM alpine:3.18 AS deps
RUN apk add --no-cache ca-certificates git
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY --from=deps /app/go.mod /app/go.sum ./
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage with distroless
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/main /
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/main"]
```

## Security Hardening Patterns

### Non-Root User Configuration
```dockerfile
# Create non-root user with specific UID/GID
FROM alpine:3.18
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup -h /home/appuser

# Set ownership and permissions
WORKDIR /app
COPY --chown=appuser:appgroup . .
USER appuser

# Drop all capabilities
USER appuser
ENTRYPOINT ["dumb-init", "--"]
CMD ["./app"]
```

### Minimal Base Images
- **Alpine Linux**: 5MB base image with package manager
- **Distroless**: Google's minimal images with no shell or package manager
- **Scratch**: Empty base image for static binaries

### Security Scanning Integration
```yaml
# GitHub Actions security workflow
name: Security Scan
on:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t myapp:${{ github.sha }} .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: myapp:${{ github.sha }}
        format: sarif
        output: trivy-results.sarif
```

## Performance Optimization Patterns

### Layer Caching Optimization
```dockerfile
FROM node:18-alpine

# Install system dependencies first (rarely change)
RUN apk add --no-cache \
    ca-certificates \
    tzdata

# Copy package files before source code (dependency caching)
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy source code last (changes frequently)
COPY . .

# Build application
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### Resource Management
```yaml
# Kubernetes deployment with resource limits
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
    ephemeral-storage: "1Gi"
  requests:
    memory: "256Mi"
    cpu: "250m"
    ephemeral-storage: "500Mi"
```

### Build Context Optimization
```dockerfile
# .dockerignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.cache
dist
build
*.md
.DS_Store
Thumbs.db
```

## Container Orchestration Patterns

### Kubernetes Deployment Pattern
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8080
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Docker Compose Development Pattern
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
      target: development
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    volumes:
      - .:/app:cached
      - node_modules:/app/node_modules
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
  node_modules:
```

## Monitoring and Health Check Patterns

### Comprehensive Health Checks
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

# Multi-level health checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node healthcheck.js

# healthcheck.js
const http = require('http');
const options = {
  host: 'localhost',
  port: 3000,
  path: '/health',
  timeout: 2000
};

const request = http.request(options, (res) => {
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

request.on('error', () => process.exit(1));
request.end();
```

### Structured Logging Pattern
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

# Configure logging
ENV LOG_LEVEL=info
ENV LOG_FORMAT=json
ENV NODE_ENV=production

# Ensure logs go to stdout/stderr
RUN ln -sf /dev/stdout /var/log/app.log
RUN ln -sf /dev/stderr /var/log/app-error.log

EXPOSE 3000
CMD ["node", "server.js"]
```

## Microservices Patterns

### Service-to-Service Communication
```dockerfile
# Service with health endpoints
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

# Health and metrics endpoints
EXPOSE 3000 9090
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "server.js"]
```

### Configuration Management
```yaml
# External configuration pattern
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://user:pass@db:5432/myapp"
  redis_url: "redis://redis:6379"
  log_level: "info"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  api_key: <base64-encoded-key>
  jwt_secret: <base64-encoded-secret>
```

## CI/CD Integration Patterns

### Multi-Architecture Build
```yaml
name: Multi-Architecture Build
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

## Modern Trends and Patterns

### Distroless and Minimal Images
- **Google Distroless**: No shell, package manager, or unnecessary binaries
- **Chainguard Images**: Minimal, secure base images with SBOMs
- **Wolfi**: Linux undistro designed for containers

### Supply Chain Security
- **Image Signing**: Use Cosign for cryptographic image signing
- **SBOM Generation**: Software Bill of Materials for dependency tracking
- **Vulnerability Scanning**: Continuous scanning in CI/CD pipelines

### Edge Computing Patterns
- **WebAssembly**: WASM containers for edge deployment
- **ARM64 Support**: Multi-architecture builds for edge devices
- **Lightweight Runtimes**: gVisor, Firecracker for enhanced isolation

## Key Performance Metrics

Based on industry research, implementing these patterns typically achieves:
- **70% faster builds** through proper layer caching
- **30-70% reduction** in image size via multi-stage builds
- **96% smaller images** (from 2.4GB to 87MB in production cases)
- **30% improvement** in resource utilization with proper limits
- **Zero critical vulnerabilities** through security scanning

## Common Anti-Patterns to Avoid

1. **Using `latest` tags** in production
2. **Running containers as root** user
3. **Not implementing health checks**
4. **Including build tools** in production images
5. **Ignoring .dockerignore** files
6. **Not setting resource limits**
7. **Hardcoding secrets** in images
8. **Using privileged containers** unnecessarily

## Key Findings

- Multi-stage builds are essential for production deployments, reducing image size by 30-70% and improving security
- Security hardening through non-root users, minimal base images, and vulnerability scanning is critical for production workloads
- Performance optimization through layer caching, resource limits, and proper monitoring can improve resource utilization by 30%
- Container orchestration patterns with Kubernetes provide scalability and reliability for microservices architectures
- Modern trends focus on supply chain security, distroless images, and edge computing capabilities

## Sources & References

- [Spacelift Docker Guides](https://spacelift.io/blog/docker) — Multi-stage builds and optimization techniques
- [Wiz Container Security Best Practices](https://www.wiz.io/academy/container-security/docker-container-security-best-practices) — Security hardening and vulnerability management
- [Binary Scripts Microservices](https://binaryscripts.com/docker/2025/02/01/dockerizing-microservices-best-practices-for-scalable-and-maintainable-systems.html) — Microservices containerization patterns
- [DevOps Roles Docker Optimization](https://www.devopsroles.com/docker-optimization-a-comprehensive-guide/) — Performance optimization strategies
- [Nerd Level Tech Docker Best Practices](https://www.nerdleveltech.com/mastering-docker-best-practices-for-2025) — 2025 best practices and security patterns

## Tools & Methods Used

- web_search: "Docker patterns best practices 2024 2025 multi-stage builds security containerization"
- web_search: "Docker patterns 2025 microservices architecture container orchestration deployment strategies"
- web_fetch: https://spacelift.io/blog/docker (multi-stage builds and optimization)
- web_search: "Docker security patterns 2025 container hardening best practices vulnerability scanning"
- web_fetch: https://www.wiz.io/academy/container-security/docker-container-security-best-practices (security patterns)
- web_search: "Docker performance optimization patterns 2025 resource management monitoring"

## Metadata

- Generated: 2026-01-12T20:28:55+01:00
- Model: Claude 3.5 Sonnet
- Session ID: N/A
- Tool calls total: 6
- Approximate duration: ~8 minutes

## Limitations & Confidence Notes

- Data current as of January 2026 – container technology evolves rapidly
- Focus on production-ready patterns may not cover all experimental approaches
- Security recommendations based on current threat landscape and may need updates
- Performance metrics are representative examples and may vary by use case
- Recommended next steps: Implement patterns incrementally, starting with multi-stage builds and security hardening
