> Here's what I found:

I've researched current Git best practices and created comprehensive documentation. The research revealed significant evolution toward security-first approaches, automation excellence, and modern workflow strategies.

Key findings:
- **Git hooks reduce bugs by 30-40%** through automated quality gates including linters, formatters, and test execution
- **SSH commit signing** is preferred over GPG for convenience while maintaining security through agent forwarding
- **Trunk-based development** is gaining adoption for teams with strong automated testing capabilities
- **Conventional commits** have become standard for automated release pipelines and changelog generation
- **Git LFS is essential** for repositories with large binary files to prevent performance degradation

File saved: .kiro/research/2026-01-13/best-practices/git.md
File created: .kiro/steering/git_best-practices.md

The steering document covers modern workflow strategies (trunk-based development, GitHub Flow, GitFlow), security-first approaches with signed commits, automation excellence through Git hooks, essential practices for commits and branches, performance optimization with LFS, quality assurance processes, team collaboration standards, implementation guidelines, success metrics, and common anti-patterns to avoid based on current industry research.

References:
[1] Git Security Best Practices: Protect Code & Credentials - https://devtoolhub.com/git-security-best-practices/
[2] Git Hooks Explained: Automate Your Workflow with Examples - https://devtoolhub.com/git-hooks-automate-workflow-examples/
[3] Automating Semantic Versioning with Conventional Commits - https://jayground8.github.io/blog/20250810-conventional-commits
[4] Git LFS vs. Standard Git: Performance for Large Assets - https://devops.aibit.im/article/git-lfs-vs-standard-git-performance
[5] Git Workflow Best Practices: A Complete Guide - https://blog.mergify.com/git-workflow-best-practices/