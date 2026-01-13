> Here's what I found:

I've researched current Rust patterns and anti-patterns, then updated the existing steering document with comprehensive anti-patterns coverage. The research revealed significant evolution toward security-first approaches and systematic anti-pattern avoidance.

Key findings:
- **Security-first development** has become critical following the Cloudflare outage caused by a single .unwrap() call
- **Memory leaks in "safe" code** through circular references and unbounded collections remain problematic
- **Async footguns** like blocking operations in async contexts are becoming more common as async adoption grows
- **Modern error handling** emphasizes designing meaningful error types rather than generic forwarding
- **Production readiness** requires systematic avoidance of panic-inducing patterns

File saved: .kiro/research/2026-01-13/patterns/rust.md
File updated: .kiro/steering/rust_patterns.md

The steering document now includes a comprehensive anti-patterns section covering the 6 most critical categories: security anti-patterns, memory management issues, ownership/borrowing problems, async footguns, error handling mistakes, and performance anti-patterns, with practical examples of both problematic and correct implementations based on current 2024-2025 research.

## Synchronization Report (Tier 2)

### Primary File Updated
- Path: .kiro/steering/rust_patterns.md
- Change type: content enhancement with comprehensive anti-patterns section
- Impact: additive

### Related Files Identified
- .kiro/steering/rust_best-practices.md - reviewed (complementary focus on patterns vs best practices)
- .kiro/steering/security_patterns.md - no change needed (general security vs Rust-specific patterns)
- .kiro/steering/error-handling_patterns.md - no change needed (general error handling vs Rust-specific patterns)

### Files Intentionally Not Checked
- Other pattern files (focus on different domains like UI, Docker, etc.)

References:
[1] The Invisible Guardian: How Rust's Borrow Checker Eradicates Entire Classes Of Cybersecurity Vulnerabilities - https://undercodetesting.com/the-invisible-guardian-how-rusts-borrow-checker-eradicates-entire-classes-of-cybersecurity-vulnerabilities/
[2] Rust Security Vulnerabilities in 2025: Comprehensive Analysis and Mitigation Strategies - https://markaicode.com/rust-security-vulnerabilities-2025-analysis-mitigation/
[3] Common Async Pitfalls in Rust Concurrency - https://www.leapcell.io/blog/common-async-pitfalls-in-rust-concurrency
[4] Anti-Patterns and Common Pitfalls - https://softwarepatternslexicon.com/rust/anti-patterns-and-common-pitfalls/recognizing-anti-patterns-in-rust/
[5] Zero-Cost Abstractions in Rust - https://dockyard.com/blog/2025/04/15/zero-cost-abstractions-in-rust-power-without-the-price