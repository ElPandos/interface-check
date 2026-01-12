# Research Output – 2026-01-12 13:35 CET

## Original Prompt
> Can you research rust best practices? and use the research file to create a .kiro/steering/rust-best-practices.md file

## Complete Response

Rust best practices focus on leveraging the language's safety guarantees, performance characteristics, and tooling ecosystem to write maintainable, efficient, and correct code. Based on current industry standards and official guidelines, here are the essential practices:

**Core Rust Best Practices:**

1. **Follow Upstream Guidelines**: Adhere to established community standards
   - Rust API Guidelines for public interfaces
   - Rust Style Guide for formatting conventions
   - Rust Design Patterns for idiomatic code structures
   - Avoid undefined behavior patterns

2. **Static Verification Tools**: Use comprehensive tooling for code quality
   - **Clippy**: 800+ lints for bug prevention and code improvement
   - **rustfmt**: Consistent source code formatting
   - **Compiler lints**: Enable additional warnings for better code quality
   - **cargo-audit**: Security vulnerability scanning
   - **cargo-hack**: Feature combination validation
   - **miri**: Unsafe code correctness validation

3. **Lint Configuration**: Enable comprehensive lint categories
   - All major clippy categories: cargo, complexity, correctness, pedantic, perf, style, suspicious
   - Selected restriction lints for consistency and quality
   - Use `#[expect]` instead of `#[allow]` to prevent stale lint overrides
   - Compiler lints: missing_debug_implementations, unsafe_op_in_unsafe_fn

4. **Type Design Principles**: Follow Rust conventions for public types
   - All public types implement `Debug` (custom implementation for sensitive data)
   - Types meant to be read implement `Display`
   - Eagerly implement common traits: Copy, Clone, Eq, PartialEq, Ord, Hash, Default
   - Use constructors as static inherent methods (Foo::new())

5. **Code Organization**: Structure for maintainability and performance
   - Prefer smaller crates over monolithic ones for compile time improvements
   - Split functionality that can be used independently
   - Use regular functions over associated functions for general computation
   - Avoid placeholder names like Service, Manager, Factory

6. **Error Handling**: Distinguish between recoverable errors and bugs
   - Panics mean "stop the program" - not for error communication
   - Use Result types for recoverable errors
   - Panic only for programming bugs or invariant violations
   - Ensure panic-safe code that maintains consistent state

7. **Documentation and Comments**: Clear communication of intent
   - Document magic numbers and constants with rationale
   - Explain why values were chosen and side effects of changes
   - Use structured logging with message templates
   - Named events with hierarchical dot-notation

8. **Performance Considerations**: Leverage Rust's zero-cost abstractions
   - Avoid unnecessary allocations in logging (use message templates)
   - Use appropriate data structures for specific use cases
   - Leverage compiler optimizations through idiomatic code
   - Profile and benchmark critical code paths

**Advanced Patterns:**

- **Ownership and Borrowing**: Master Rust's ownership system
  - Prefer borrowing over cloning when possible
  - Use lifetime parameters appropriately
  - Understand when to use Rc/Arc for shared ownership

- **Trait Design**: Create flexible and composable interfaces
  - Use trait objects for dynamic dispatch when needed
  - Implement standard traits consistently
  - Design traits for extensibility

- **Unsafe Code**: When necessary, ensure correctness
  - Document all unsafe blocks with safety comments
  - Use miri for validation
  - Minimize unsafe code surface area
  - Provide safe abstractions over unsafe operations

**Tooling Integration:**

```toml
[lints.rust]
missing_debug_implementations = "warn"
unsafe_op_in_unsafe_fn = "warn"
unused_lifetimes = "warn"

[lints.clippy]
cargo = { level = "warn", priority = -1 }
complexity = { level = "warn", priority = -1 }
correctness = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
perf = { level = "warn", priority = -1 }
style = { level = "warn", priority = -1 }
suspicious = { level = "warn", priority = -1 }
```

**Development Workflow:**
- Use `cargo fmt` for consistent formatting
- Run `cargo clippy` on every commit
- Enable all relevant lints in Cargo.toml
- Use `cargo test` for comprehensive testing
- Integrate tools into CI/CD pipeline

**Industry Examples:**
- **Microsoft**: Comprehensive Rust guidelines with static verification
- **Google**: Rust style guide integration with existing tooling
- **Mozilla**: Servo project demonstrating large-scale Rust best practices
- **Dropbox**: File storage systems leveraging Rust's safety guarantees

**Common Anti-Patterns to Avoid:**
- Using `unwrap()` in production code without justification
- Ignoring compiler warnings and clippy suggestions
- Over-using `unsafe` code without proper documentation
- Creating overly complex type hierarchies
- Not implementing common traits for public types

These practices ensure Rust code is safe, performant, and maintainable while leveraging the language's unique strengths in systems programming.

## Key Findings
- Rust's tooling ecosystem (clippy, rustfmt, miri) provides 800+ lints for comprehensive code quality
- Static verification tools should be integrated into every Rust project's workflow
- Panics are for program termination, not error handling - use Result types for recoverable errors
- Smaller crates improve compile times and modularity significantly

## Sources & References
- [Pragmatic Rust Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/universal/) — Microsoft's comprehensive Rust development guidelines
- [Code Formatting and Linting with rustfmt and clippy](https://codeforgeek.com/rustfmt-and-clippy-in-rust/) — tooling integration guide
- [Rust Language Features and Best Practices](https://softwarepatternslexicon.com/rust/rust-language-features-and-best-practices/coding-style-and-conventions/) — coding style and conventions
- [Write Cleaner Rust Code Using Clippy and Idiomatic Practices](https://moldstud.com/articles/p-enhance-your-rust-coding-skills-how-clippy-can-help-you-write-idiomatic-rust-code) — clippy best practices

## Tools & Methods Used
- web_search: "Rust best practices 2026 coding standards clippy rustfmt"
- web_fetch: https://microsoft.github.io/rust-guidelines/guidelines/universal/

## Metadata
- Generated: 2026-01-12T13:35:32+01:00
- Model: Claude (Kiro CLI)
- Tool calls total: 2
- Approximate duration: ~3 minutes

## Limitations & Confidence Notes
- Data current as of January 2026 – Rust ecosystem evolves rapidly with new tooling
- Guidelines may vary based on project type (systems programming vs web development)
- Recommended next steps: Implement tooling integration and establish team conventions
