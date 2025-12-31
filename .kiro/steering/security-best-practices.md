---
title: Security Best Practices
inclusion: always
---

# Security Best Practices

## Code Security
- Never hardcode secrets, API keys, or SSH passwords
- Use environment variables for SSH credentials and configuration
- Validate all user inputs, especially network interface names and IP addresses
- Implement proper SSH key-based authentication where possible
- Use connection timeouts and retry limits for SSH connections

## Dependency Management
- Keep dependencies updated
- Use dependency scanning tools
- Review third-party packages before adding
- Use lock files (uv.lock, requirements.lock)
- Remove unused dependencies

## Data Protection
- Encrypt sensitive data at rest and in transit
- Use HTTPS for all web communications
- Implement proper session management
- Use secure headers (HSTS, CSP, etc.)
- Follow OWASP guidelines

## Infrastructure Security
- Use least privilege principle for IAM
- Enable logging and monitoring
- Use network segmentation
- Implement proper backup strategies
- Regular security audits and penetration testing

## Development Practices
- Use static code analysis tools
- Implement security testing in CI/CD
- Code reviews for security issues
- Security training for developers
- Incident response procedures
