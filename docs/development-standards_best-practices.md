---
title:        Development Standards Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Development Standards Best Practices

## Core Principles

### 1. Type Safety First
Static type checking catches errors before runtime. Use type hints comprehensively with strict type checkers (mypy --strict, pyright). Type annotations serve as living documentation and enable IDE tooling.

### 2. Shift-Left Quality
Embed quality at every development stage rather than treating it as a post-deployment concern. Automated testing, linting, and security scanning should run on every commit, not just before release.

### 3. SOLID Design
Apply Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion principles. These create maintainable, extensible systems that survive changing requirements.

### 4. Continuous Delivery Readiness
Code should always be deployable. Small, frequent changes reduce risk. Production readiness includes monitoring hooks, security scans, load testing, and documented rollback procedures.

### 5. Security by Design
Security is not a feature—it's a property. Validate all inputs, encode outputs, use parameterized queries, implement least-privilege access, and encrypt sensitive data at rest and in transit.

## Essential Practices

### Code Quality Standards

**Type Annotations**
- Annotate all function signatures, class attributes, and module-level variables
- Use `from __future__ import annotations` for forward references
- Prefer `TypedDict`, `dataclasses`, or Pydantic models over raw dicts
- Run type checkers in CI with strict mode enabled

**Formatting & Linting**
- Use automated formatters (ruff format, black) with zero configuration drift
- Enforce linting rules via pre-commit hooks and CI gates
- Configure line length consistently (88 or 120 characters)
- Ban commented-out code and unused imports

**Documentation**
- Write Google-style docstrings for all public APIs
- Document non-obvious behavior, edge cases, and performance characteristics
- Keep README files current with setup, usage, and architecture overview
- Generate API documentation automatically from docstrings

### Testing Strategy

**Test Pyramid**
- Unit tests: Fast, isolated, cover business logic (70-80% of tests)
- Integration tests: Verify component interactions (15-25%)
- End-to-end tests: Validate critical user journeys (5-10%)

**Test Quality**
- Tests must be deterministic—no flaky tests in CI
- Use fixtures and factories, not production data copies
- Mock external dependencies at boundaries, not deep in code
- Measure coverage but optimize for mutation testing effectiveness

**Test-Driven Development**
- Write failing tests before implementation for complex logic
- Use tests as executable specifications
- Refactor only when tests pass

### CI/CD Pipeline Standards

**Automation Requirements**
- Every commit triggers: lint, type check, unit tests, security scan
- Pull requests require: integration tests, code review approval
- Deployments include: smoke tests, canary releases, automated rollback

**Pipeline Quality Gates**
- Block merges on test failures, type errors, or security vulnerabilities
- Enforce minimum coverage thresholds (80%+ line coverage)
- Require signed commits and verified authors
- Scan dependencies for known vulnerabilities (Dependabot, Snyk)

### Code Review Standards

**Review Focus Areas**
1. Correctness: Does it solve the stated problem?
2. Security: Input validation, authentication, authorization
3. Performance: Algorithmic complexity, resource usage
4. Maintainability: Readability, testability, documentation
5. Architecture: Adherence to patterns, separation of concerns

**Review Process**
- Keep PRs small (<400 lines of meaningful changes)
- Provide context in PR descriptions with linked issues
- Use automated tools for style—humans review logic
- Require at least one approval from code owner
- Address all comments before merge

### Security Practices

**OWASP Top 10 Compliance**
- Validate and sanitize all user inputs
- Use parameterized queries—never string concatenation for SQL
- Implement proper authentication with MFA support
- Apply least-privilege access control
- Encrypt sensitive data; never log secrets

**Dependency Management**
- Pin dependency versions in lock files
- Audit dependencies weekly for vulnerabilities
- Minimize dependency count—each adds attack surface
- Prefer well-maintained libraries with security track records

**Secrets Management**
- Never commit secrets to version control
- Use environment variables or secrets managers
- Rotate credentials regularly
- Audit secret access logs

## Anti-Patterns to Avoid

### Code Quality Anti-Patterns
- **Any-typing**: Using `Any` to bypass type checking defeats the purpose
- **God classes**: Classes with too many responsibilities become unmaintainable
- **Primitive obsession**: Using raw strings/dicts instead of domain types
- **Copy-paste programming**: Duplicated code diverges and rots
- **Magic numbers/strings**: Unexplained literals obscure intent

### Testing Anti-Patterns
- **Testing implementation**: Tests coupled to internal structure break on refactoring
- **Flaky tests**: Non-deterministic tests erode trust in CI
- **Test data coupling**: Tests sharing mutable state cause cascade failures
- **Excessive mocking**: Over-mocked tests don't verify real behavior
- **Missing edge cases**: Happy-path-only tests miss production failures

### Process Anti-Patterns
- **Big-bang releases**: Large, infrequent deployments increase risk
- **Review bottlenecks**: PRs waiting days for review slow delivery
- **Manual deployments**: Human-driven releases introduce errors
- **Ignored warnings**: Suppressed linter/type errors accumulate debt
- **Documentation drift**: Outdated docs mislead more than no docs

### Security Anti-Patterns
- **Security through obscurity**: Hidden endpoints are still vulnerable
- **Trusting client input**: All external data is potentially malicious
- **Logging sensitive data**: Credentials in logs become breach vectors
- **Hardcoded secrets**: Secrets in code persist in version history
- **Disabled security features**: Turning off HTTPS/CORS "for testing"

## Implementation Guidelines

### Phase 1: Foundation (Week 1-2)
1. Configure linter (ruff) and formatter with team-agreed rules
2. Set up pre-commit hooks for automated checks
3. Enable strict type checking in CI pipeline
4. Establish PR template with required sections
5. Document coding standards in repository

### Phase 2: Testing Infrastructure (Week 3-4)
1. Configure test framework with coverage reporting
2. Set minimum coverage thresholds (start at 60%, increase to 80%)
3. Add integration test suite for critical paths
4. Implement test fixtures and factories
5. Enable mutation testing for critical modules

### Phase 3: CI/CD Hardening (Week 5-6)
1. Add security scanning (SAST, dependency audit)
2. Implement automated deployment pipeline
3. Configure canary releases and rollback automation
4. Set up monitoring and alerting for deployments
5. Document runbooks for common failure scenarios

### Phase 4: Continuous Improvement (Ongoing)
1. Review DORA metrics monthly
2. Conduct quarterly security audits
3. Update dependencies on regular schedule
4. Refactor based on code quality metrics
5. Train team on emerging best practices

### Tooling Recommendations

**Python Stack**
- Formatter: ruff format
- Linter: ruff check
- Type checker: mypy --strict or pyright
- Testing: pytest with pytest-cov
- Security: bandit, safety, pip-audit

**CI/CD**
- GitHub Actions, GitLab CI, or equivalent
- Dependabot or Renovate for dependency updates
- SonarQube or CodeClimate for quality metrics

## Success Metrics

### DORA Metrics (DevOps Research and Assessment)

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| Deployment Frequency | On-demand (multiple/day) | Weekly-Monthly | Monthly-Quarterly | <Quarterly |
| Lead Time for Changes | <1 hour | 1 day-1 week | 1 week-1 month | >1 month |
| Change Failure Rate | 0-15% | 16-30% | 31-45% | >45% |
| Time to Restore | <1 hour | <1 day | 1 day-1 week | >1 week |

### Code Quality Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Test Coverage | >80% | 60-80% | <60% |
| Type Coverage | >95% | 80-95% | <80% |
| Cyclomatic Complexity | <10 | 10-20 | >20 |
| Technical Debt Ratio | <5% | 5-10% | >10% |
| Dependency Vulnerabilities | 0 critical | 1-2 critical | >2 critical |

### Process Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| PR Review Time | <4 hours | 4-24 hours | >24 hours |
| PR Size | <400 lines | 400-800 lines | >800 lines |
| Build Time | <10 min | 10-30 min | >30 min |
| Flaky Test Rate | 0% | <1% | >1% |

### Measurement Approach
1. Automate metric collection in CI/CD pipeline
2. Display metrics on team dashboard
3. Review trends weekly in team standups
4. Set quarterly improvement targets
5. Celebrate improvements, investigate regressions

## Sources & References

- [AWS Code Quality Explained](https://aws.amazon.com/what-is/code-quality/) — Definition and importance of code quality metrics
- [Cortex Software Quality Metrics](https://www.cortex.io/post/software-quality-metrics) — 18 metrics to track in 2025
- [Cortex Code Review Best Practices](https://www.cortex.io/post/best-practices-for-code-reviews) — Sustainable code review approaches
- [Cortex Production Readiness](https://www.cortex.io/report/the-2024-state-of-software-production-readiness) — 2024 state of production readiness
- [OWASP Top Ten](https://owasp.org/www-project-top-ten/) — Web application security risks
- [OWASP Secure Coding Practices](https://owasp.org/www-project-developer-guide/release/appendices/implementation_dos_donts/secure_coding/) — Developer security guidelines
- [DORA Metrics Guide](https://blog.codacy.com/dora-metrics-to-accelerate-software-delivery) — Measuring DevOps performance
- [LaunchDarkly DORA Metrics](https://launchdarkly.com/blog/dora-metrics/) — Four key DevOps measurements
- [Clean Code Principles](https://www.pullchecklist.com/posts/clean-code-principles) — SOLID and maintainability in 2025
- [Software Design Best Practices](https://www.docuwriter.ai/posts/software-design-best-practices) — Essential design principles for 2025
- [Type-Driven Development](https://www.leapcell.io/blog/type-driven-development-in-python-with-pydantic-and-mypy) — Python type hints with Pydantic and MyPy
- [Python Type Hints Guide](https://www.propelcode.ai/blog/python-type-hints-code-review-guide-mypy-best-practices) — Type hints in code review
- [CI/CD Security](https://cloudnativenow.com/contributed-content/why-secure-by-design-ci-cd-matters-in-cloud-native-systems/) — Secure-by-design pipelines
- [End-to-End Testing 2026](https://www.thehansindia.com/tech/end-to-end-testing-in-2026-best-practices-for-faster-releases-and-fewer-production-bugs-1037758) — Testing best practices for faster releases

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
