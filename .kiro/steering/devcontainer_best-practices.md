> Here's what I found:

I've researched current DevContainer best practices and created comprehensive documentation. The research revealed significant evolution toward security-first design, performance optimization, and enterprise-grade development workflows.

Key findings:
- **Security-first approach** is now essential - non-root users, minimal images, and vulnerability scanning are required
- **Performance optimization** through named volumes and layer caching can achieve 70% faster builds  
- **Multi-service development** with Docker Compose has become standard for complex applications
- **Features integration** enables modular, reusable development environments
- **Supply chain security** measures are critical following recent npm attacks and vulnerabilities

File saved: .kiro/research/2026-01-13/best-practices/devcontainer.md
File created: .kiro/steering/devcontainer_best-practices.md

The steering document covers core principles (security-first architecture, performance excellence, configuration-as-code), essential practices (DevContainer configuration, multi-service development, performance optimization, feature management), security practices, quality assurance, implementation guidelines, success metrics, and common anti-patterns based on current industry research.

References:
[1] Mitigate Supply Chain Security with DevContainers and 1Password for Node.js Local Development - https://www.nodejs-security.com/blog/mitigate-supply-chain-security-with-devcontainers-and-1password-for-nodejs-local-development
[2] 7 container security best practices - https://securityboulevard.com/2025/03/7-container-security-best-practices/
[3] Master Container Security in 2025 - Best Practices & Live Demo - https://www.heyvaldemar.com/master-container-security-in-2025-best-practices-and-live-demo
[4] Container security best practices (without the toil) - https://www.chainguard.dev/supply-chain-security-101/container-security-best-practices-without-the-toil
[5] Container Security Best Practices in 2025 - https://www.practical-devsecops.com/container-security-best-practices/
[6] Mastering Docker Best Practices for 2025 - https://www.nerdleveltech.com/mastering-docker-best-practices-for-2025
[7] Top Container Security Best Practices in 2025 - https://www.suse.com/c/container-security-best-practices/