---
title:        Git Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Git Best Practices

## Core Principles

1. **Atomic Commits**: Each commit represents exactly one logical change—self-contained, focused, and independently revertable. Never mix unrelated changes.

2. **Conventional Commits**: Use structured commit messages with type prefixes (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`) for automated changelog generation and semantic versioning.

3. **Trunk-Based Development**: Prefer short-lived feature branches (< 2 days) merging frequently to main. ~70% of modern teams use trunk-based over GitFlow for CI/CD compatibility.

4. **Security First**: Never commit secrets. Use `.gitignore`, pre-commit hooks (git-secrets), and signed commits for cryptographic authorship verification.

5. **Clean History**: Maintain readable, linear history through strategic rebasing of private branches and squash merging for feature completion.

## Essential Practices

### Commit Messages

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no logic change)
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding/correcting tests
- `build`: Build system/dependencies
- `ci`: CI configuration
- `chore`: Maintenance tasks
- `revert`: Revert previous commit

**Rules:**
- Subject line: imperative mood, ≤50 characters, no period
- Body: wrap at 72 characters, explain *what* and *why*
- Breaking changes: add `!` after type or `BREAKING CHANGE:` footer

### Branching Strategy

**Trunk-Based (Recommended for CI/CD):**
```
main ─────●─────●─────●─────●─────●
           \   /       \   /
            ●─●         ●─●
         feature-a   feature-b
         (1-2 days)  (1-2 days)
```

**GitHub Flow (Simple teams):**
- `main` always deployable
- Feature branches from main
- PR → review → merge → deploy

**GitFlow (Complex releases):**
- `main`: production releases
- `develop`: integration branch
- `feature/*`, `release/*`, `hotfix/*`
- Use only when release cycles require it

### Merge Strategy

| Scenario | Strategy | Rationale |
|----------|----------|-----------|
| Feature → main | Squash merge | Clean single commit |
| Shared branch | Merge commit | Preserve history |
| Private branch sync | Rebase | Linear history |
| Hotfix | Merge commit | Audit trail |

**Golden Rule**: Never rebase public/shared branches.

### Security Practices

```bash
# Pre-commit secret scanning
git secrets --install
git secrets --register-aws

# GPG signed commits
git config --global commit.gpgsign true
git config --global user.signingkey <KEY_ID>

# Global gitignore for secrets
echo "*.pem\n*.key\n.env\n.env.*\nsecrets/\n*.secret" >> ~/.gitignore_global
git config --global core.excludesfile ~/.gitignore_global
```

**If secrets are committed:**
1. Rotate the exposed credentials immediately
2. Use `git filter-repo` to purge from history
3. Force push and notify collaborators
4. Consider repository compromise

## Anti-Patterns to Avoid

### Commit Anti-Patterns
- ❌ `"fix"`, `"update"`, `"WIP"` as commit messages
- ❌ Mixing multiple unrelated changes in one commit
- ❌ Committing generated files, build artifacts, or dependencies
- ❌ Large commits that are difficult to review or revert
- ❌ Committing directly to main without review

### Branching Anti-Patterns
- ❌ Long-lived feature branches (> 1 week)
- ❌ Rebasing shared/public branches
- ❌ Force pushing to main or shared branches
- ❌ Not deleting merged branches
- ❌ Inconsistent branch naming conventions

### Security Anti-Patterns
- ❌ Hardcoding secrets, API keys, or credentials
- ❌ Ignoring pre-commit hook failures
- ❌ Using unsigned commits in security-sensitive repos
- ❌ Not scanning for secrets before pushing
- ❌ Assuming `.gitignore` protects already-committed files

## Implementation Guidelines

### 1. Repository Setup

```bash
# Initialize with main branch
git init
git branch -M main

# Configure user identity
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Enable commit signing
git config commit.gpgsign true

# Set default branch
git config init.defaultBranch main

# Configure pull behavior
git config pull.rebase true
```

### 2. Pre-commit Hooks

```bash
# Install pre-commit framework
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
      - id: detect-private-key
      - id: check-merge-conflict
  - repo: https://github.com/awslabs/git-secrets
    rev: master
    hooks:
      - id: git-secrets
EOF

pre-commit install
```

### 3. Branch Workflow

```bash
# Create feature branch
git checkout -b feature/add-user-auth

# Make atomic commits
git add -p  # Stage interactively
git commit -m "feat(auth): add JWT token validation"

# Keep branch updated (private branch)
git fetch origin
git rebase origin/main

# Push and create PR
git push -u origin feature/add-user-auth
```

### 4. Code Review Process

1. **Author responsibilities:**
   - Self-review diff before requesting review
   - Write clear PR description with context
   - Keep PRs small (< 400 lines ideal)
   - Respond to feedback promptly

2. **Reviewer responsibilities:**
   - Review within 24 hours
   - Focus on logic, security, and maintainability
   - Use conventional comments (nitpick, suggestion, blocking)
   - Approve only when confident

### 5. Release Tagging

```bash
# Semantic versioning tags
git tag -a v1.2.0 -m "Release v1.2.0: Add user authentication"
git push origin v1.2.0

# Annotated tags for releases (signed)
git tag -s v1.2.0 -m "Release v1.2.0"
```

## Success Metrics

### Commit Quality
- **Atomic commit rate**: % of commits with single logical change (target: >95%)
- **Conventional commit compliance**: % following format (target: 100%)
- **Average commit size**: Lines changed per commit (target: <100)

### Branch Health
- **Branch lifetime**: Average days before merge (target: <3 days)
- **Merge conflict rate**: % of PRs with conflicts (target: <10%)
- **Stale branch count**: Branches >30 days old (target: 0)

### Security
- **Secret detection rate**: Secrets caught pre-commit (target: 100%)
- **Signed commit rate**: % of commits signed (target: 100% for main)
- **Time to rotate**: Hours to rotate exposed secrets (target: <1 hour)

### Collaboration
- **PR review time**: Hours from open to first review (target: <24h)
- **PR size**: Average lines per PR (target: <400)
- **Merge frequency**: Merges to main per day (target: multiple)

## Sources & References

- [Conventional Commits Specification](https://www.conventionalcommits.org) — Standard commit message format
- [Git Tower: Perfect Commit Message](https://www.git-tower.com/blog/how-to-write-the-perfect-commit-message/) — Atomic commits guidance
- [Mergify: Trunk-Based vs GitFlow](https://mergify.com/blog/trunk-based-development-vs-gitflow-which-branching-model-actually-works) — Modern branching comparison
- [DevToolHub: Git Security](https://devtoolhub.com/git-security-best-practices/) — Security practices
- [Graphite: PR Merge Strategy](https://graphite.dev/blog/pull-request-merge-strategy) — Merge strategy selection
- [DataCamp: Merge vs Rebase](https://www.datacamp.com/blog/git-merge-vs-git-rebase) — Integration strategy comparison
- [SpectralOps: Git Secrets](https://spectralops.io/blog/how-to-use-git-secrets-for-better-code-security/) — Secret scanning setup

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
