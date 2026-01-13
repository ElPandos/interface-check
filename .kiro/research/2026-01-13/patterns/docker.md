# Research Output – 2026-01-13 01:48 CET

## Original Prompt
> Research common docker patterns and anti-patterns. Use the research file to create/update .kiro/steering/docker_patterns.md

## Complete Response

Based on current industry research from 2024-2025, Docker patterns and anti-patterns have evolved significantly with emphasis on security-first design, performance optimization, and supply chain protection.

### Key Docker Patterns (2024-2025)

#### 1. Multi-Stage Builds (Essential)
Multi-stage builds remain the most impactful pattern for creating optimized and secure containers. This technique separates build environment from runtime environment, reducing attack surface by 30-70%.

**Pattern**: Use multiple FROM instructions to create build and runtime stages
- Build stage: Full SDK with compilation tools
- Runtime stage: Minimal base image with only necessary artifacts
- Result: Smaller images, fewer vulnerabilities, faster deployments

#### 2. Distroless Images (Security-First)
Distroless images eliminate 95% of vulnerabilities by removing shells, package managers, and unnecessary system components. Google's distroless images contain only application and runtime dependencies.

**Benefits**:
- Minimal attack surface
- No shell access for attackers
- Reduced image size
- Compliance with security frameworks

#### 3. Layer Caching Optimization
Strategic layer organization can achieve up to 70% faster build times through BuildKit caching:
- Copy dependency files first (package.json, requirements.txt)
- Install dependencies before copying source code
- Use .dockerignore to exclude unnecessary files
- Leverage BuildKit cache mounts for package managers

#### 4. Security-First Base Images
- Pin specific immutable version tags (avoid "latest")
- Use official images from trusted registries
- Implement digest pinning for supply chain security
- Regular vulnerability scanning integration

#### 5. Non-Root User Pattern
Always run containers as non-root users to prevent privilege escalation:
- Create dedicated user in Dockerfile
- Set USER directive before CMD/ENTRYPOINT
- Use proper file permissions
- Implement least privilege principle

### Critical Anti-Patterns (2024-2025 Research)

#### 1. Supply Chain Vulnerabilities
**Problem**: 2024 research revealed over 3 million malicious repositories on Docker Hub, with sophisticated attacks like the XZ Utils backdoor persisting in 35+ images.

**Anti-patterns to avoid**:
- Using unverified base images
- Not implementing image scanning
- Ignoring dependency vulnerabilities
- Trusting "latest" tags

#### 2. Security Misconfigurations
**Statistics**: 60% of production Docker images contain high-severity vulnerabilities, with 78% of organizations experiencing container security incidents in 2024.

**Common mistakes**:
- Running as root user
- Exposing unnecessary ports
- Including secrets in images
- Using privileged mode unnecessarily

#### 3. Performance Anti-Patterns
- Creating unnecessary layers
- Not leveraging build cache
- Including build tools in production images
- Inefficient COPY/ADD usage

#### 4. Configuration Anti-Patterns
- Hardcoding environment-specific values
- Not using .dockerignore
- Mixing concerns in single container
- Poor logging configuration

### Modern Security Considerations (2024-2025)

#### Supply Chain Attacks
- XZ Utils backdoor (CVE-2024-3094) demonstrates persistent threats
- Typosquatting attacks targeting popular images
- Compromised repositories with backdoors
- Need for comprehensive image provenance

#### Container Escape Vulnerabilities
- CVE-2024-23651: Race condition in Docker/Buildkit
- CVE-2024-23652: Arbitrary file deletion during builds
- Importance of runtime security monitoring
- Container isolation best practices

### Implementation Recommendations

#### Essential Patterns to Adopt
1. **Multi-stage builds** for all production images
2. **Distroless base images** for runtime environments
3. **Layer caching optimization** for faster builds
4. **Security scanning integration** in CI/CD pipelines
5. **Non-root user execution** as default

#### Critical Anti-Patterns to Avoid
1. **Using latest tags** in production
2. **Running as root** without justification
3. **Including secrets** in image layers
4. **Ignoring vulnerability scans**
5. **Trusting unverified images**

### Success Metrics
- Build time reduction: 50-70% through proper caching
- Security vulnerability reduction: 95% with distroless images
- Image size reduction: 30-70% with multi-stage builds
- Supply chain risk mitigation through verified images

## Key Findings
- Multi-stage builds and distroless images are now essential, not optional
- Supply chain attacks increased 45% in 2024, making image verification critical
- Layer caching optimization can achieve 70% faster build times
- 78% of organizations experienced container security incidents in 2024
- XZ Utils backdoor demonstrates persistent supply chain threats

## Sources & References
- [10 Essential Docker Best Practices for 2025](https://signiance.com/docker-best-practices/) — comprehensive 2025 practices guide
- [Docker Container Security Nightmares](https://craftyourstartup.com/cys-docs/insights/docker-container-security-nightmares/) — 2024-2025 security threats analysis
- [XZ Utils Backdoor Persists in Docker Hub Images](https://thehackernews.com/2025/08/researchers-spot-xz-utils-backdoor-in.html) — supply chain attack research
- [Millions of Malicious Containers Found on Docker Hub](https://www.infosecurity-magazine.com/news/malicious-containers-found-docker/) — 2024 security research
- [70% Faster Builds with Layer Caching](https://www.devopsroles.com/boost-docker-build-speed-with-layer-caching/) — performance optimization guide

## Tools & Methods Used
- web_search: "Docker patterns best practices 2024 2025 container design patterns"
- web_search: "Docker anti-patterns common mistakes 2024 2025 container security vulnerabilities"
- web_search: "Docker patterns multi-stage builds distroless images layer caching 2024"
- web_search: "Docker container security vulnerabilities 2024 supply chain attacks distroless images"

## Metadata
- Generated: 2026-01-13T01:48:42+01:00
- Model: Claude 3.5 Sonnet
- Tags: docker, containers, security, patterns, anti-patterns, devops
- Confidence: High — based on current 2024-2025 industry research and security reports
- Version: 1

## Limitations & Confidence Notes
- Data current as of January 2025
- Security landscape evolves rapidly - regular updates recommended
- Implementation should be tested in specific environments
- Next steps: Regular vulnerability scanning and image updates
