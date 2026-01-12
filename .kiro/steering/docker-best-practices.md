---
title:        Docker Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Docker Best Practices

## Purpose
Establish comprehensive Docker containerization practices for building secure, efficient, and maintainable applications in production environments.

## Core Principles

### 1. Image Building and Optimization
- **Multi-Stage Builds**: Separate build environment from runtime to reduce image size and attack surface
- **Minimal Base Images**: Use Alpine Linux, distroless, or scratch images instead of full OS images
- **Layer Optimization**: Minimize layers and combine RUN commands efficiently
- **Build Context**: Use .dockerignore to exclude unnecessary files
- **Reproducible Builds**: Ensure builds are deterministic and reproducible

### 2. Security Hardening
- **Non-Root Users**: Always create and use dedicated non-root users for applications
- **Read-Only Root Filesystem**: Configure containers with read-only root filesystems
- **Security Contexts**: Implement proper security contexts with least privilege
- **Capability Management**: Drop all capabilities and add only necessary ones
- **No Privileged Containers**: Avoid running containers in privileged mode

### 3. Resource Management
- **Resource Limits**: Set CPU, memory, and storage limits for all containers
- **Health Checks**: Implement proper health checks for container monitoring
- **Restart Policies**: Configure appropriate restart policies
- **Signal Handling**: Ensure applications handle termination signals gracefully

## Image Building Best Practices

### 1. Multi-Stage Dockerfile Example
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
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["npm", "start"]
```

### 2. Base Image Selection
```dockerfile
# Bad: Full Ubuntu image with unnecessary packages
FROM ubuntu:20.04

# Good: Minimal Alpine Linux base
FROM alpine:3.18

# Better: Distroless images for maximum security
FROM gcr.io/distroless/java:11

# Best: Scratch for static binaries
FROM scratch
```

### 3. Layer Optimization
```dockerfile
# Bad: Multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# Good: Combined operations
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

## Security Configuration

### 1. Security Context (Kubernetes)
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
```

### 2. Resource Limits
```yaml
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

### 3. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

## Secrets Management

### 1. Environment Variables vs Secrets
```dockerfile
# Bad: Hardcoded secrets
ENV DATABASE_PASSWORD=supersecret123

# Good: Use secret management systems
ENV DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

### 2. Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database-password: <base64-encoded-password>
---
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: database-password
```

## Monitoring and Logging

### 1. Health Checks
```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Custom script health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD /app/healthcheck.sh || exit 1
```

### 2. Structured Logging
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: my-app:latest
    env:
    - name: LOG_LEVEL
      value: "INFO"
    - name: LOG_FORMAT
      value: "json"
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  - name: log-forwarder
    image: fluent/fluent-bit:latest
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
      readOnly: true
```

## CI/CD Integration

### 1. Security Scanning Pipeline
```yaml
# GitHub Actions security workflow
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t my-app:${{ github.sha }} .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: my-app:${{ github.sha }}
        format: sarif
        output: trivy-results.sarif
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: trivy-results.sarif
    
    - name: Docker Scout scan
      uses: docker/scout-action@v1
      with:
        command: cves
        image: my-app:${{ github.sha }}
```

### 2. Image Signing
```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Sign image with Cosign
cosign sign --key cosign.key my-registry/my-app:latest

# Verify signed image
cosign verify --key cosign.pub my-registry/my-app:latest
```

## Advanced Security Techniques

### 1. Pod Security Standards
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 2. Runtime Security Monitoring
```yaml
# Falco rule for detecting suspicious activity
- rule: Detect shell in container
  desc: Detect shell activity in containers
  condition: >
    spawned_process and container and
    (proc.name in (shell_binaries) or
     proc.name in (shell_mgmt_binaries))
  output: >
    Shell spawned in container (user=%user.name container=%container.name
    shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
  priority: WARNING
```

## Common Anti-Patterns to Avoid

### 1. Image Building Issues
- Using `latest` tags in production
- Not using multi-stage builds for compiled applications
- Including build tools in production images
- Not optimizing layer caching
- Ignoring .dockerignore files

### 2. Security Issues
- Running containers as root user
- Using privileged containers unnecessarily
- Hardcoding secrets in images
- Not implementing health checks
- Exposing unnecessary ports

### 3. Resource Management Issues
- Not setting resource limits
- Using inappropriate restart policies
- Not handling signals properly
- Ignoring container lifecycle management

## Production Deployment Guidelines

### 1. Orchestration Best Practices
- Use Kubernetes or similar orchestration platforms
- Implement proper service discovery
- Configure load balancing and traffic routing
- Set up horizontal pod autoscaling
- Plan for rolling updates and rollbacks

### 2. Storage and Persistence
- Use persistent volumes for stateful applications
- Implement proper backup strategies
- Configure storage classes appropriately
- Plan for data migration scenarios

### 3. Networking and Service Mesh
- Implement service mesh for advanced traffic management
- Use mutual TLS for service-to-service communication
- Configure ingress controllers properly
- Implement proper DNS resolution

## Compliance and Governance

### 1. Security Policies
- Implement Pod Security Policies or Pod Security Standards
- Use admission controllers for policy enforcement
- Regular security audits and compliance checks
- Maintain audit trails for all changes

### 2. Image Management
- Use private container registries
- Implement image scanning and vulnerability management
- Maintain image provenance and supply chain security
- Regular base image updates and patching

## Version History

- v1.0 (2026-01-12): Initial version based on industry best practices and production deployment experiences
