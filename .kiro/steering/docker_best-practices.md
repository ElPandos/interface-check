> Here's what I found:

I've researched current Docker best practices and created comprehensive documentation. The research revealed significant evolution toward security-first approaches, performance optimization, and production-ready deployment patterns.

Key findings:
- **Distroless images** eliminate 95% of vulnerabilities by removing shells, package managers, and unnecessary utilities
- **Supply chain attacks** targeting container registries have increased, making digest pinning and signature verification critical
- **BuildKit 2.0** can achieve up to 70% faster builds through advanced caching techniques
- **Multi-stage builds** provide 30-70% attack surface reduction by separating build and runtime environments
- **Health checks** reduce downtime by 50% when properly implemented with comprehensive monitoring

File saved: .kiro/research/2026-01-13/best-practices/docker.md
File created: .kiro/steering/docker_best-practices.md

The steering document covers security-first architecture (distroless images, supply chain verification, vulnerability management), performance optimization (BuildKit features, layer caching, runtime optimization), production deployment excellence (health checks, orchestration integration, monitoring), development workflows, quality assurance practices, implementation guidelines, success metrics, and common anti-patterns based on current industry research.

References:
[1] Mastering Docker Best Practices for 2025 - https://www.nerdleveltech.com/mastering-docker-best-practices-for-2025
[2] 10 Essential Docker Best Practices for 2025 - https://signiance.com/docker-best-practices/
[3] Enterprise-Grade Docker: Production Hardening and Optimization Techniques - https://devopsservices.io/blog/docker-best-practices
[4] Docker Security Hardening in Production - https://codingtricks.io/docker-security-hardening-production-guide/
[5] Why Docker Hardened Images Are a Game-Changer for Software Supply Chain Security - https://kifarunix.com/why-docker-hardened-images-are-a-game-changer-for-software-supply-chain-security/
[6] 70% Faster Builds with Layer Caching Better 2025 - https://www.devopsroles.com/boost-docker-build-speed-with-layer-caching/
[7] How to Use BuildKit 2.0 Effectively in 2025: Step-by-Step Tutorial - https://skywork.ai/blog/how-to-use-buildkit-2-0-effectively-in-2025-step-by-step-tutorial/
[8] 10 Docker Healthcheck Best Practices - https://climbtheladder.com/10-docker-healthcheck-best-practices/