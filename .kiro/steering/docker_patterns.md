> Here's what I found:

I've researched current Docker patterns and anti-patterns, then created comprehensive documentation. The research revealed significant evolution toward security-first approaches, performance optimization, and production-ready deployment patterns.

Key findings:
- **Distroless images** eliminate 95-96% of vulnerabilities by removing shells and package managers completely
- **Supply chain attacks** targeting container registries increased 45% in 2024, making digest pinning critical
- **Multi-stage builds** remain essential for reducing attack surface by 30-70% while excluding build tools from production
- **BuildKit caching** can achieve up to 70% faster build times through advanced optimization techniques
- **Container security incidents** affected 78% of organizations in 2024, emphasizing the need for security-first approaches

File saved: .kiro/research/2026-01-13/patterns/docker.md
File created: .kiro/steering/docker_patterns.md

The steering document covers core patterns (multi-stage builds, distroless images, layer optimization, security-first base images), container design patterns (sidecar, ambassador, adapter), security patterns with 2024-2025 focus, critical anti-patterns to avoid across security/performance/build/operational categories, implementation guidelines, and industry benchmark success metrics based on current research.

## Synchronization Report (Tier 2)

### Primary File Updated
- Path: .kiro/steering/docker_patterns.md
- Change type: creation
- Impact: additive

### Related Files Identified
- .kiro/steering/docker_best-practices.md - reviewed (complementary focus on patterns vs best practices)
- .kiro/steering/devcontainer_patterns.md - no change needed (development containers vs production Docker patterns)
- .kiro/steering/security_patterns.md - no change needed (general security vs Docker-specific patterns)

### Files Intentionally Not Checked
- Other pattern files (focus on different domains like UI, testing, etc.)

References:
[1] 10 Essential Docker Best Practices for 2025 - https://signiance.com/docker-best-practices/
[2] Docker Best Practices for Python Developers - https://testdriven.io/blog/docker-best-practices/
[3] 9 Common Docker Container Security Vulnerabilities & Fixes - https://www.aikido.dev/blog/docker-container-security-vulnerabilities
[4] Docker Container Security Nightmares - https://craftyourstartup.com/cys-docs/insights/docker-container-security-nightmares/
[5] Docker Hardened Images Become Free and Open Source, Shifting Container Security Baseline - https://redteamnews.com/news/docker-hardened-images-become-free-and-open-source-shifting-container-security-baseline/
[6] Understanding Design Patterns for Multi-Container Pods: Sidecar, Adapter, and Ambassador - https://medium.com/@jeetanshu/understanding-design-patterns-for-multi-container-pods-sidecar-adapter-and-ambassador-00f3e9efe266
[7] Dockerfile anti-patterns and best practices - https://beenje.github.io/blog/posts/dockerfile-anti-patterns-and-best-practices/