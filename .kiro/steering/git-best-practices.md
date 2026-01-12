---
title:        Git Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Git Best Practices

## Purpose
Establish standardized Git workflow practices for maintaining clean, collaborative, and efficient development processes.

## Core Practices

### 1. Branching Strategy
- **Git Flow**: Use main, develop, feature/*, release/*, hotfix/* branches for complex projects
- **GitHub Flow**: Simpler approach with main and feature/* branches for continuous deployment
- Document chosen strategy clearly for team consistency
- Use branch protection rules to enforce policies

### 2. Commit Messages
- **Format**: Use conventional commit format: `type: description`
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Length**: Keep subject line under 50 characters
- **Style**: Use imperative mood ("Add feature" not "Added feature")
- **Traceability**: Include ticket numbers when applicable

### 3. Code Reviews
- **Mandatory**: All changes must go through pull/merge requests
- **No Direct Pushes**: Prevent direct commits to main/master branch
- **Approval Required**: Minimum one reviewer approval before merging
- **Automated Checks**: Integrate CI/CD pipeline with branch protection
- **Documentation**: Maintain audit trail of all changes

### 4. Commit Structure
- **Atomic Commits**: Each commit represents single logical change
- **Complete State**: Every commit should leave codebase in working condition
- **Frequent Commits**: Commit at logical stopping points during development
- **Partial Staging**: Use `git add -p` for focused commits

### 5. Branch Naming
- **Prefixes**: Use consistent prefixes (feature/, bugfix/, hotfix/, release/)
- **Descriptive**: Include clear description of work being done
- **Format**: Use lowercase with hyphens for readability
- **Examples**: `feature/user-authentication`, `bugfix/login-validation`

### 6. Repository Management
- **Regular Pushes**: Push changes at least daily to remote repository
- **Clean History**: Use feature branches for incomplete work
- **Branch Cleanup**: Delete merged branches to maintain organization
- **Gitignore**: Exclude build artifacts, dependencies, and sensitive files

## Implementation Guidelines

### Branch Protection Rules
- Require pull request reviews before merging
- Dismiss stale reviews when new commits are pushed
- Require status checks to pass before merging
- Restrict push access to protected branches
- Enable admin override for emergency situations

### Commit Best Practices
- Test each commit individually when possible
- Use `git stash` to manage work in progress
- Split large changes into logical steps
- Write descriptive commit messages explaining "why" not just "what"

### Team Workflow
- Establish and document team conventions
- Provide training on chosen practices
- Use templates for consistent formatting
- Regular review and cleanup of repository
- Automate enforcement where possible

## Benefits
- **Code Quality**: Improved through mandatory reviews and testing
- **Collaboration**: Enhanced team communication and knowledge sharing
- **Maintainability**: Cleaner history and easier debugging
- **Traceability**: Clear audit trail of all changes
- **Automation**: Enables automated changelog generation and deployment

## Common Pitfalls to Avoid
- Large, monolithic commits that bundle unrelated changes
- Cryptic commit messages that don't explain purpose
- Direct pushes to main branch bypassing review process
- Inconsistent branch naming conventions
- Committing sensitive data or build artifacts

## Version History

- v1.0 (2026-01-12): Initial version based on industry research and best practices
