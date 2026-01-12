# Research Output – 2026-01-12 13:45 CET

## Original Prompt
> Can you research docker best practices? and use the research file to create a .kiro/steering/docker-best-practices.md file

## Complete Response

Docker best practices encompass comprehensive strategies for building secure, efficient, and maintainable containerized applications. Based on current industry standards and production deployment experiences, here are the essential practices:

**Core Docker Best Practices:**

1. **Image Building and Optimization**: Foundation for efficient containers
   - **Multi-Stage Builds**: Separate build environment from runtime to reduce image size and attack surface
   - **Minimal Base Images**: Use Alpine Linux, distroless, or scratch images instead of full OS images
   - **Layer Optimization**: Minimize layers and combine RUN commands to reduce image size
   - **Build Context**: Use .dockerignore to exclude unnecessary files from build context
   - **Image Scanning**: Implement vulnerability scanning with tools like Trivy, Docker Scout, or Clair

2. **Security Hardening**: Protect containers and host systems
   - **Non-Root Users**: Always create and use dedicated non-root users for applications
   - **Read-Only Root Filesystem**: Configure containers with read-only root filesystems
   - **Security Contexts**: Implement proper security contexts with least privilege
   - **Capability Dropping**: Drop all capabilities and add only necessary ones
   - **No Privileged Containers**: Avoid running containers in privileged mode
   - **Secrets Management**: Never hardcode secrets; use proper secret management systems

3. **Resource Management**: Prevent resource exhaustion and ensure stability
   - **Resource Limits**: Set CPU, memory, and storage limits for all containers
   - **Health Checks**: Implement proper health checks for container monitoring
   - **Restart Policies**: Configure appropriate restart policies for different scenarios
   - **Process Management**: Use proper init systems for multi-process containers
   - **Signal Handling**: Ensure applications handle termination signals gracefully

4. **Network Security**: Secure container communications
   - **Network Policies**: Implement Kubernetes network policies for traffic control
   - **Service Mesh**: Use service mesh (Istio, Linkerd) for advanced security features
   - **TLS Encryption**: Encrypt all inter-service communications
   - **Port Exposure**: Expose only necessary ports and use non-privileged ports
   - **Network Segmentation**: Isolate containers using proper network segmentation

5. **Container Registry Security**: Secure image distribution
   - **Private Registries**: Use private container registries for proprietary images
   - **Image Signing**: Implement image signing with Docker Content Trust or Cosign
   - **Registry Authentication**: Secure registry access with proper authentication
   - **Vulnerability Scanning**: Scan images before deployment
   - **Image Provenance**: Maintain clear image provenance and supply chain security

6. **Monitoring and Logging**: Comprehensive observability
   - **Structured Logging**: Use structured logging formats (JSON) for better parsing
   - **Log Aggregation**: Centralize logs using tools like Fluentd, Fluent Bit, or Logstash
   - **Metrics Collection**: Implement metrics collection with Prometheus or similar tools
   - **Runtime Security**: Use runtime security tools like Falco for threat detection
   - **Audit Logging**: Enable comprehensive audit logging for compliance

7. **Development and CI/CD Integration**: Secure development workflows
   - **Automated Security Scanning**: Integrate security scanning into CI/CD pipelines
   - **Image Vulnerability Gates**: Fail builds on critical vulnerabilities
   - **Dependency Management**: Keep base images and dependencies updated
   - **Build Reproducibility**: Ensure builds are reproducible and deterministic
   - **Supply Chain Security**: Verify integrity of base images and dependencies

**Advanced Security Techniques:**

- **Pod Security Standards**: Implement Kubernetes Pod Security Standards (restricted profile)
- **Admission Controllers**: Use admission controllers for policy enforcement
- **Runtime Protection**: Deploy runtime protection tools for real-time threat detection
- **Zero Trust Architecture**: Implement zero trust principles for container communications
- **Compliance Frameworks**: Align with security frameworks (CIS, NIST, SOC 2)

**Multi-Stage Build Example:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Production stage
FROM node:18-alpine AS production
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
USER nextjs
EXPOSE 3000
CMD ["npm", "start"]
```

**Security Context Configuration:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
```

**Resource Limits:**
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

**Common Anti-Patterns to Avoid:**

- Using `latest` tags in production
- Running containers as root user
- Hardcoding secrets in images or environment variables
- Using full OS images when minimal images suffice
- Ignoring security vulnerabilities in base images
- Not implementing proper health checks
- Exposing unnecessary ports or services
- Using privileged containers without justification
- Not setting resource limits
- Storing sensitive data in container layers

**Production Deployment Considerations:**

- **Orchestration**: Use Kubernetes or similar orchestration platforms
- **High Availability**: Design for fault tolerance and redundancy
- **Scaling**: Implement horizontal pod autoscaling
- **Storage**: Use persistent volumes for stateful applications
- **Backup and Recovery**: Implement proper backup strategies
- **Disaster Recovery**: Plan for disaster recovery scenarios

**Compliance and Governance:**

- **Policy as Code**: Implement security policies as code
- **Compliance Scanning**: Regular compliance checks against standards
- **Audit Trails**: Maintain comprehensive audit trails
- **Access Controls**: Implement proper RBAC and access controls
- **Change Management**: Establish proper change management processes

These practices ensure Docker containers are secure, efficient, and maintainable in production environments while following industry security standards.

## Key Findings
- Multi-stage builds significantly reduce image size and attack surface by separating build and runtime environments
- Running containers as non-root users is critical for security - privilege escalation attacks are a major risk
- Distroless and minimal base images (Alpine) provide better security than full OS images
- Comprehensive security scanning should be integrated into CI/CD pipelines with vulnerability gates

## Sources & References
- [Docker Security Hardening in Production](https://codingtricks.io/docker-security-hardening-production-guide/) — comprehensive production security guide
- [Best Practices for Dockerfile Multi-Stage Builds](https://kb.rnd.sh/dockerfile-multi-stage-best-practices) — multi-stage build security considerations
- [Best Practices for Building Docker Images](https://betterstack.com/community/guides/scaling-docker/docker-build-best-practices/) — image optimization techniques
- [Docker Security Hardening Guide](https://www.voguesoftwares.com/dockerGuide) — container security hardening techniques

## Tools & Methods Used
- web_search: "Docker best practices 2026 containerization security multi-stage builds"
- web_fetch: https://codingtricks.io/docker-security-hardening-production-guide/

## Metadata
- Generated: 2026-01-12T13:45:29+01:00
- Model: Claude (Kiro CLI)
- Tool calls total: 2
- Approximate duration: ~3 minutes

## Limitations & Confidence Notes
- Data current as of January 2026 – Docker ecosystem and security practices continue evolving
- Security recommendations may vary based on specific deployment environments and compliance requirements
- Recommended next steps: Implement multi-stage builds and establish comprehensive security scanning in CI/CD pipelines
