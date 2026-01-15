---
title:        Git Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Git Patterns

## Core Principles

1. **Atomic Commits**: Each commit should represent a single logical change. One commit = one purpose. This enables clean reverts, bisects, and code reviews.

2. **Meaningful History**: Commit history is documentation. Write messages that explain *why*, not just *what*. Future developers (including yourself) will thank you.

3. **Branch Isolation**: Never work directly on main/master. Feature branches isolate changes until they're ready for integration.

4. **Frequent Integration**: Sync with upstream regularly. Long-lived branches accumulate merge debt exponentially.

5. **Never Commit Secrets**: Credentials, API keys, and sensitive data must never enter version control. Use `.gitignore` from day one.

## Essential Patterns

### Branching Strategies

**Trunk-Based Development (Recommended for CI/CD)**
- Single main branch with short-lived feature branches (< 2 days)
- Developers integrate small, frequent changes multiple times daily
- Requires strong CI/CD pipeline and feature flags
- Best for: Teams practicing continuous deployment

**GitHub Flow**
- Simple: main + feature branches
- Feature branches merge via pull requests
- Best for: Small to medium teams, web applications

**GitFlow**
- Structured: main, develop, feature/*, release/*, hotfix/*
- Supports parallel development and scheduled releases
- Best for: Projects with formal release cycles, multiple versions in production

### Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature (correlates with MINOR in SemVer)
- `fix`: Bug fix (correlates with PATCH in SemVer)
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change that neither fixes nor adds
- `perf`: Performance improvement
- `test`: Adding/correcting tests
- `chore`: Maintenance tasks

**Rules:**
- Subject line: imperative mood, ≤50 characters, no period
- Body: wrap at 72 characters, explain *why* not *what*
- Footer: reference issues, note breaking changes

**Example:**
```
feat(auth): add OAuth2 support for GitHub login

Implement GitHub OAuth2 flow to allow users to authenticate
using their GitHub accounts. This reduces friction for
developers who already have GitHub accounts.

Closes #123
BREAKING CHANGE: removes legacy session-based auth
```

### Merge vs Rebase

**Use Merge When:**
- Integrating shared/public branches
- Preserving complete history is important
- Working with less experienced team members

**Use Rebase When:**
- Cleaning up local commits before PR
- Updating feature branch with latest main
- Creating linear, readable history

**Interactive Rebase for Cleanup:**
```bash
git rebase -i HEAD~n  # Squash last n commits
```
- `pick`: Keep commit as-is
- `squash`: Combine with previous commit
- `fixup`: Squash without keeping message
- `reword`: Change commit message

### Pull Request Workflow

1. Create feature branch from latest main
2. Make atomic commits with clear messages
3. Rebase/squash to clean history before PR
4. Push and create pull request
5. Address review feedback (amend or new commits)
6. Squash-merge or rebase-merge to main
7. Delete feature branch

## Anti-Patterns to Avoid

### Commit Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Giant commits | Impossible to review, hard to revert | Commit early, commit often |
| "WIP" commits on main | Pollutes history, breaks bisect | Use feature branches |
| Vague messages ("fix", "update") | No context for future debugging | Follow commit conventions |
| Committing generated files | Bloats repo, causes conflicts | Proper `.gitignore` |
| Committing secrets | Security breach, permanent exposure | Pre-commit hooks, git-secrets |

### Branch Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Long-lived feature branches | Merge hell, integration pain | Trunk-based or short branches |
| Working on main directly | No isolation, risky deploys | Always use branches |
| Not syncing with upstream | Divergence, massive conflicts | Pull/rebase daily |
| Orphaned branches | Clutter, confusion | Delete after merge |

### History Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Force push to shared branches | Destroys teammates' work | Use `--force-with-lease` only on personal branches |
| Rebasing public history | Breaks everyone's local copies | Only rebase unpushed commits |
| Merge commits in feature branches | Messy history | Rebase to update feature branches |
| Never squashing | Noisy PR history | Squash before merge |

### Workflow Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| No code review | Quality issues, knowledge silos | Mandatory PR reviews |
| Huge PRs | Review fatigue, bugs slip through | Small, focused PRs (< 400 lines) |
| No CI on branches | Broken main | Branch protection + CI gates |
| Manual deployments | Human error, inconsistency | Automated pipelines |

## Implementation Guidelines

### Repository Setup

1. **Initialize with essentials:**
   ```bash
   git init
   echo "# Project Name" > README.md
   curl -o .gitignore https://gitignore.io/api/python,node,macos,linux
   git add -A && git commit -m "chore: initial commit"
   ```

2. **Configure branch protection:**
   - Require PR reviews before merge
   - Require status checks to pass
   - Require linear history (optional)
   - Prevent force pushes to main

3. **Set up hooks:**
   ```bash
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/pre-commit/pre-commit-hooks
       hooks:
         - id: check-added-large-files
         - id: detect-private-key
         - id: trailing-whitespace
   ```

### Daily Workflow

```bash
# Start new work
git checkout main && git pull
git checkout -b feature/short-description

# Work in atomic commits
git add -p  # Stage hunks interactively
git commit -m "feat(scope): description"

# Stay current
git fetch origin
git rebase origin/main

# Before PR: clean up
git rebase -i origin/main  # Squash/fixup as needed

# Push and create PR
git push -u origin feature/short-description
```

### Handling Mistakes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Amend last commit
git commit --amend

# Recover deleted branch
git reflog  # Find commit hash
git checkout -b recovered-branch <hash>

# Undo pushed commit (safe)
git revert <commit-hash>

# Force push safely (personal branch only)
git push --force-with-lease
```

## Success Metrics

### Quantitative Metrics

| Metric | Target | Why |
|--------|--------|-----|
| PR size | < 400 lines changed | Reviewable, lower defect rate |
| PR cycle time | < 24 hours | Fast feedback, less context switching |
| Branch lifetime | < 2 days | Reduces merge conflicts |
| Build success rate | > 95% | CI/CD health |
| Commit frequency | Multiple per day | Atomic changes, continuous progress |

### Qualitative Indicators

- **Clean `git log`**: Can understand project evolution by reading history
- **Easy bisect**: Can find bug-introducing commits quickly
- **Painless merges**: Conflicts are rare and small
- **Confident reverts**: Can undo changes without side effects
- **Onboarding speed**: New developers understand workflow quickly

### Code Review Health

- Reviews completed within 24 hours
- Constructive feedback, not nitpicking
- Knowledge sharing happening in reviews
- No rubber-stamping (meaningful review comments)

## Sources & References

- [Conventional Commits Specification](https://www.conventionalcommits.org/en/v1.0.0/) — Standard format for commit messages
- [DZone Git Patterns and Anti-Patterns](https://dzone.com/refcardz/git-patterns-and-anti-patterns) — Comprehensive patterns reference
- [Trunk-Based Development vs GitFlow](https://graphite.com/guides/trunk-vs-gitflow) — Branching strategy comparison
- [Git Best Practices Guide](https://toxigon.com/git-best-practices-guide) — General best practices overview
- [How You Can Go Wrong with Git](https://www.freecodecamp.org/news/how-you-can-go-wrong-with-git-and-what-to-do-instead-d80eeeff1d95/) — Common mistakes and solutions
- [Git Rebase vs Merge](https://zapier.com/blog/git-rebase-vs-merge/) — When to use each approach
- [Security Best Practices for Git](https://www.codingrules.ai/rules/security-best-practices-standards-for-git) — Security guidelines
- [.gitignore Best Practices](https://gitignore.pro/guides/gitignore-best-practices) — Ignore file patterns

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
