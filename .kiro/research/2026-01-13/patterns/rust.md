# Research Output – 2026-01-13 05:26 CET

## Original Prompt
> Research common rust patterns and anti-patterns. Use the research file to create/update .kiro/steering/rust_patterns.md

## Complete Response

Based on current research from 2024-2025, Rust patterns and anti-patterns have evolved significantly with growing enterprise adoption and Microsoft's commitment to replace C/C++ with Rust by 2030. The research reveals critical insights into memory safety, performance optimization, and systematic approaches to avoiding common pitfalls.

### Core Rust Patterns

**1. RAII (Resource Acquisition Is Initialization)**
- Resource initialization in constructor, cleanup in destructor
- Extended in Rust through guard objects that mediate access via type system
- Prevents resource leaks through automatic cleanup when guards go out of scope

**2. Newtype Pattern**
- Wraps existing types to provide additional type safety and validation
- Enables compile-time guarantees for domain-specific constraints
- Example: `struct Email(String)` with validation in constructor

**3. Builder Pattern**
- Constructs complex objects step by step with method chaining
- Handles optional parameters elegantly without telescoping constructors
- Returns `Result<T, E>` for fallible construction

**4. Error Handling Patterns**
- `Result<T, E>` for operations that can fail
- `Option<T>` for values that might be absent
- Custom error types with proper error propagation using `?` operator
- Avoid error forwarding anti-pattern - design errors for specific contexts

**5. Ownership and Borrowing Patterns**
- Single ownership with automatic cleanup
- Borrowing through references (`&T` and `&mut T`)
- Lifetime parameters for complex reference relationships
- Move semantics for transferring ownership

### Critical Anti-Patterns to Avoid

**1. Performance Anti-Patterns**
- **Unnecessary cloning**: Using `clone()` instead of borrowing kills performance
- **String vs &str misuse**: Using `&String` parameters instead of `&str` reduces API flexibility
- **Excessive allocations**: Not using `Cow<'a, T>` for read-heavy scenarios
- **Ignoring zero-cost abstractions**: Writing C-style code instead of idiomatic Rust

**2. Memory Safety Anti-Patterns**
- **Unsafe code abuse**: Bypassing borrow checker without proper justification
- **Lifetime issues**: Fighting the borrow checker instead of designing around ownership
- **Dangling references**: Returning references to local variables
- **Use-after-free patterns**: Accessing moved values

**3. Error Handling Anti-Patterns**
- **Panic abuse**: Using `unwrap()` and `expect()` in production code
- **Error swallowing**: Ignoring `Result` types without proper handling
- **Generic error forwarding**: Not designing context-specific error types
- **Exception-style thinking**: Trying to replicate try-catch patterns

**4. API Design Anti-Patterns**
- **Taking ownership unnecessarily**: Using `String` parameters instead of `&str`
- **Returning owned data**: Using `Vec<T>` returns instead of iterators
- **Inflexible APIs**: Not using generic parameters where appropriate
- **Blocking APIs**: Not providing async alternatives for I/O operations

**5. Concurrency Anti-Patterns**
- **Shared mutable state**: Not using proper synchronization primitives
- **Arc<Mutex<T>> overuse**: Using when simpler alternatives exist
- **Blocking in async**: Mixing blocking and async code incorrectly
- **Thread spawning**: Creating threads instead of using thread pools

### Modern Rust Considerations (2024-2025)

**Enterprise Adoption Patterns**
- Microsoft's C/C++ to Rust migration reveals systematic approaches
- Memory safety eliminates 70% of security vulnerabilities
- AI-assisted migration tools becoming standard
- Focus on gradual migration strategies

**Performance-First Design**
- Profile-first optimization methodology
- Cache-friendly data structures and access patterns
- Zero-allocation hot paths where possible
- Proper use of `Cow<'a, T>` for read-heavy workloads

**Error Design Evolution**
- Moving from error forwarding to context-specific error design
- Structured error types that support multiple failure modes
- Error categorization for better debugging and monitoring
- Integration with observability systems

## Key Findings

- **Memory Safety Revolution**: Rust's ownership system eliminates entire classes of vulnerabilities at compile time
- **Performance Through Safety**: Zero-cost abstractions enable high-level code with C-level performance
- **Error Handling Maturity**: Moving beyond simple Result/Option to sophisticated error design
- **Enterprise Readiness**: Large-scale adoption patterns emerging with systematic migration strategies
- **Anti-Pattern Recognition**: Focus on prevention through proper design rather than detection

## Sources & References

- [Stop Forwarding Errors, Start Designing Them](https://fast.github.io/blog/stop-forwarding-errors-start-designing-them/) — Error design evolution + access date: 2026-01-13
- [Rust Code Review Checklist: Ownership, Borrowing, and Safety](https://pullpanda.io/blog/rust-code-review-checklist) — Performance anti-patterns + access date: 2026-01-13
- [Anti-Patterns and Common Pitfalls](https://softwarepatternslexicon.com/rust/anti-patterns-and-common-pitfalls/recognizing-anti-patterns-in-rust/) — Systematic anti-pattern recognition + access date: 2026-01-13
- [RAII Guards and Newtypes in Rust](https://benjamincongdon.me/blog/2025/12/23/RAII-Guards-and-Newtypes-in-Rust/) — Modern pattern implementations + access date: 2026-01-13
- [Turbocharge Rust Performance: The Optimal Use of &str and &[T] Slices](https://openillumi.com/en/en-rust-performance-avoid-ref-string-vec/) — Performance optimization patterns + access date: 2026-01-13
- [10 Rust Performance Tips: From Basics to Advanced](https://leapcell.io/blog/10-rust-performance-tips) — Performance best practices + access date: 2026-01-13
- [9 Rust Pitfalls Every Developer Should Know](https://www.leapcell.io/blog/nine-rust-pitfalls) — Common mistakes and solutions + access date: 2026-01-13

## Tools & Methods Used

- web_search: "Rust programming patterns anti-patterns 2024 2025 best practices common mistakes"
- web_search: "Rust design patterns common anti-patterns ownership borrowing error handling 2024"
- web_search: "\"Rust anti-patterns\" \"common mistakes\" \"bad practices\" 2024 2025 performance memory safety"
- web_search: "Rust programming patterns RAII builder pattern newtype pattern error handling Result Option 2024"
- web_search: "Rust performance anti-patterns clone unnecessary allocations String vs str lifetime issues 2024"

## Metadata

- Generated: 2026-01-13T05:26:22+01:00
- Model: Claude 3.5 Sonnet
- Tags: rust, patterns, anti-patterns, memory-safety, performance, error-handling
- Confidence: High - based on comprehensive 2024-2025 research from authoritative sources
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Focus on patterns relevant to enterprise adoption and performance
- Anti-patterns based on real-world production experience
- Next steps: Monitor evolution of async patterns and WASM integration
