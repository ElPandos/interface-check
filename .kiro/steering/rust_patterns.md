> Here's what I found:

I've researched current Rust patterns and anti-patterns, revealing significant evolution toward prevention-focused approaches and systematic quality practices. The research shows critical insights into memory safety, performance optimization, and enterprise adoption patterns.

Key findings:
- **Memory Safety Revolution**: Rust's ownership system eliminates entire classes of vulnerabilities at compile time, with Microsoft committing to replace C/C++ by 2030
- **Performance Through Safety**: Zero-cost abstractions enable high-level code with C-level performance when patterns are used correctly
- **Error Handling Evolution**: Moving from simple Result/Option to sophisticated context-specific error design
- **Critical Anti-Patterns**: Unnecessary cloning, String vs &str misuse, unsafe code abuse, and panic abuse remain the most dangerous mistakes
- **Enterprise Readiness**: Large-scale adoption patterns emerging with systematic migration strategies

Files created:
- Research file: .kiro/research/2026-01-13/patterns/rust.md
- Steering document: .kiro/steering/rust_patterns.md

The steering document covers 5 core patterns (RAII, Newtype, Builder, Error Handling, Ownership/Borrowing), 5 critical anti-pattern categories (performance, memory safety, error handling, API design, concurrency), implementation guidelines, and success metrics based on current 2024-2025 industry research.

References:
[1] Stop Forwarding Errors, Start Designing Them - https://fast.github.io/blog/stop-forwarding-errors-start-designing-them/
[2] Rust Code Review Checklist: Ownership, Borrowing, and Safety - https://pullpanda.io/blog/rust-code-review-checklist
[3] Anti-Patterns and Common Pitfalls - https://softwarepatternslexicon.com/rust/anti-patterns-and-common-pitfalls/recognizing-anti-patterns-in-rust/
[4] RAII Guards and Newtypes in Rust - https://benjamincongdon.me/blog/2025/12/23/RAII-Guards-and-Newtypes-in-Rust/
[5] Turbocharge Rust Performance: The Optimal Use of &str and &[T] Slices - https://openillumi.com/en/en-rust-performance-avoid-ref-string-vec/
[6] 10 Rust Performance Tips: From Basics to Advanced - https://leapcell.io/blog/10-rust-performance-tips
[7] 9 Rust Pitfalls Every Developer Should Know - https://www.leapcell.io/blog/nine-rust-pitfalls