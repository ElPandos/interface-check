# Research Output – 2026-01-13 00:47 CET

## Original Prompt
> Research best rust practices. Use the research file to create/update .kiro/steering/rust_best-practices.md

## Complete Response

Based on comprehensive research of current Rust development practices in 2025-2026, here are the essential best practices for modern Rust development:

## Core Rust Principles

### 1. Memory Safety Without Garbage Collection
Rust's fundamental value proposition is providing memory safety guarantees at compile time without runtime overhead. The ownership system prevents entire classes of bugs including use-after-free, double-free, and data races.

### 2. Zero-Cost Abstractions
High-level constructs compile down to efficient machine code matching the performance of manually written low-level code. This allows developers to use powerful abstractions like traits, generics, and iterators without performance penalties.

### 3. Fearless Concurrency
Rust's ownership system enables safe concurrent programming by preventing data races at compile time, allowing developers to write parallel code with confidence.

## Ownership and Memory Management

### Ownership Rules
- Every value has exactly one owner at any time
- When the owner goes out of scope, the value is automatically cleaned up
- Ownership can be transferred (moved) but not duplicated for heap-allocated types

### Borrowing Best Practices
- Use immutable references (`&T`) when you only need to read data
- Use mutable references (`&mut T`) when you need to modify data
- Follow the borrowing rules: multiple immutable references OR one mutable reference, never both
- Keep borrow scopes as short as possible to avoid lifetime conflicts

### Smart Pointers
- Use `Box<T>` for heap allocation when you need owned data
- Use `Rc<T>` for shared ownership in single-threaded contexts
- Use `Arc<T>` for shared ownership in multi-threaded contexts
- Use `RefCell<T>` for interior mutability when needed

## Error Handling Excellence

### Result and Option Types
- Use `Result<T, E>` for operations that can fail
- Use `Option<T>` for values that might be absent
- Avoid `unwrap()` and `expect()` in production code - handle errors explicitly
- Use the `?` operator for clean error propagation

### Custom Error Types
- Implement the `Error` trait for custom error types
- Use `thiserror` crate for simple error types
- Use `anyhow` crate for application-level error handling
- Provide meaningful error messages with context

### Error Handling Patterns
```rust
// Good: Explicit error handling
match operation() {
    Ok(value) => process(value),
    Err(e) => handle_error(e),
}

// Good: Using ? operator
fn process_data() -> Result<String, MyError> {
    let data = read_file()?;
    let processed = transform_data(data)?;
    Ok(processed)
}
```

## Async Programming with Tokio

### Async Best Practices
- Use `async`/`await` for I/O-bound operations
- Prefer `tokio::spawn` for CPU-bound tasks that need to run concurrently
- Use `tokio::select!` for handling multiple async operations
- Avoid blocking operations in async contexts

### Performance Considerations
- Use `tokio::task::spawn_blocking` for CPU-intensive work
- Prefer `Arc<Mutex<T>>` over `Rc<RefCell<T>>` in async contexts
- Use channels (`tokio::sync::mpsc`) for communication between tasks
- Consider using `tokio::time::timeout` for operations that might hang

## Testing Excellence

### Test Organization
- Use `#[cfg(test)]` modules for unit tests
- Place integration tests in the `tests/` directory
- Use descriptive test names that explain the scenario being tested
- Follow the Arrange-Act-Assert pattern

### Testing Tools
- Use `cargo test` for running tests
- Use `#[should_panic]` for tests that expect panics
- Use `proptest` for property-based testing
- Use `mockall` for mocking dependencies

### Benchmarking
- Use `criterion` crate for accurate benchmarking
- Profile before optimizing with tools like `perf` or `flamegraph`
- Use `cargo bench` for running benchmarks
- Focus on algorithmic improvements over micro-optimizations

## Code Quality and Tooling

### Essential Tools
- **rustfmt**: Automatic code formatting following Rust style guidelines
- **clippy**: Linting tool that catches common mistakes and suggests improvements
- **cargo check**: Fast compilation check without generating binaries
- **cargo doc**: Generate documentation from code comments

### CI/CD Integration
- Run `cargo clippy -- -D warnings` to treat warnings as errors
- Use `cargo fmt --check` to verify formatting in CI
- Include `cargo test` and `cargo bench` in your pipeline
- Use `cargo audit` to check for security vulnerabilities

### Code Organization
- Use modules to organize related functionality
- Keep public APIs minimal and well-documented
- Use `pub(crate)` for internal APIs
- Follow Rust naming conventions (snake_case for functions, PascalCase for types)

## Performance Optimization

### Profiling-First Approach
- Always profile before optimizing
- Use tools like `perf`, `valgrind`, or `flamegraph`
- Focus on algorithmic improvements over micro-optimizations
- Measure the impact of optimizations

### Memory Efficiency
- Prefer `&str` over `String` for read-only string data
- Use `Vec::with_capacity()` when the size is known
- Consider using `Box<[T]>` instead of `Vec<T>` for fixed-size collections
- Use iterators instead of collecting into vectors when possible

### Compilation Optimization
- Use `cargo build --release` for production builds
- Consider link-time optimization (LTO) for final releases
- Use `codegen-units = 1` for maximum optimization
- Profile-guided optimization (PGO) for critical applications

## Security Best Practices

### Safe Rust Practices
- Minimize use of `unsafe` code
- When using `unsafe`, document safety invariants clearly
- Use `#[must_use]` for types that should not be ignored
- Validate all inputs at system boundaries

### Dependency Management
- Regularly audit dependencies with `cargo audit`
- Pin dependency versions in production
- Use `cargo deny` to enforce licensing and security policies
- Keep dependencies up to date

### Secure Coding
- Avoid `unwrap()` in production code to prevent panics
- Use constant-time comparison for cryptographic operations
- Be careful with integer overflow in release mode
- Validate all external inputs thoroughly

## Modern Rust Ecosystem

### Essential Crates
- **serde**: Serialization and deserialization
- **tokio**: Async runtime and utilities
- **clap**: Command-line argument parsing
- **log** + **env_logger**: Logging infrastructure
- **thiserror** + **anyhow**: Error handling

### Web Development
- **axum** or **actix-web**: Web frameworks
- **tower**: Service abstractions and middleware
- **hyper**: HTTP implementation
- **sqlx**: Async SQL toolkit

### System Programming
- **crossbeam**: Lock-free data structures and utilities
- **rayon**: Data parallelism
- **mio**: Low-level I/O
- **nix**: Unix system calls

## Common Anti-Patterns to Avoid

### Memory Management Issues
- Excessive use of `clone()` instead of borrowing
- Fighting the borrow checker with `Rc<RefCell<T>>` everywhere
- Using `unsafe` to bypass borrow checker instead of redesigning
- Not understanding when moves occur

### Error Handling Mistakes
- Using `unwrap()` and `expect()` in production code
- Ignoring `Result` types (compiler warnings about unused results)
- Not providing context in error messages
- Using `panic!` for recoverable errors

### Performance Issues
- Unnecessary allocations in hot paths
- Not using iterators effectively
- Premature optimization without profiling
- Blocking async tasks with synchronous operations

### Code Organization Problems
- Monolithic modules without clear boundaries
- Public APIs that expose implementation details
- Inconsistent naming conventions
- Missing documentation for public APIs

## Implementation Guidelines

### Getting Started
- Start with safe Rust and only use `unsafe` when absolutely necessary
- Use `clippy` and `rustfmt` from day one
- Write tests alongside your code
- Read compiler error messages carefully - they're usually helpful

### Team Development
- Establish coding standards and use `rustfmt` for consistency
- Use `clippy` in CI to catch common issues
- Conduct code reviews focusing on API design and error handling
- Share knowledge about Rust idioms and best practices

### Production Deployment
- Use `cargo build --release` for production builds
- Set up monitoring and logging
- Have a plan for handling panics in production
- Regular security audits of dependencies

## Key Takeaways

1. **Embrace the Ownership System**: Don't fight the borrow checker; redesign your code to work with it
2. **Error Handling is Not Optional**: Use `Result` and `Option` types properly, avoid `unwrap()` in production
3. **Profile Before Optimizing**: Rust is fast by default, focus on algorithmic improvements
4. **Use the Ecosystem**: Leverage high-quality crates instead of reinventing the wheel
5. **Safety First**: Minimize `unsafe` code and document safety invariants when you must use it
6. **Test Everything**: Rust's type system catches many bugs, but you still need comprehensive tests
7. **Async When Appropriate**: Use async for I/O-bound operations, not CPU-bound tasks
8. **Documentation Matters**: Write clear documentation for public APIs and complex algorithms

## Key Findings

- Rust's ownership system eliminates entire classes of memory safety bugs at compile time
- Zero-cost abstractions allow high-level programming without performance penalties
- Modern tooling (clippy, rustfmt, cargo) provides excellent developer experience
- Async programming with Tokio enables highly concurrent applications
- Security requires more than memory safety - proper error handling and input validation are critical

## Sources & References

- [Rust Best Practices - Cursor Rules](https://www.cursorrules.org/article/rust-cursor-mdc-file) — Comprehensive development guidelines
- [Rust Memory Management 2025](https://dasroot.net/posts/2025/12/rust-memory-management-explained/) — Modern memory management patterns
- [Tokio Async Best Practices](https://www.leapcell.io/blog/tokio-futures-async-rust) — Zero-cost async programming
- [Rust Error Handling Mastery](https://toxigon.com/rust-error-handling-best-practices) — Result and Option patterns
- [Rust Security Best Practices 2025](https://corgea.com/Learn/rust-security-best-practices-2025) — Security-focused development
- [Rust Performance Optimization](https://webreference.com/rust/systems/performance/) — Zero-cost abstractions and benchmarking
- [Cargo Tools and Workflow](https://codeforgeek.com/cargo-tips-and-tricks-for-rust-projects/) — Modern tooling practices

## Tools & Methods Used

- web_search: "Rust best practices 2025 2026 modern development guidelines"
- web_search: "Rust ownership patterns memory safety best practices 2025"
- web_search: "Rust async programming tokio best practices 2025"
- web_search: "Rust error handling Result Option best practices 2025"
- web_search: "Rust testing cargo clippy rustfmt tooling best practices 2025"
- web_search: "Rust performance optimization zero cost abstractions benchmarking 2025"
- web_search: "Rust security practices unsafe code memory safety 2025"

## Metadata

- Generated: 2026-01-13T00:47:12+01:00
- Model: Claude 3.5 Sonnet
- Tags: rust, best-practices, memory-safety, async, performance, security
- Confidence: High - based on comprehensive research of current Rust ecosystem and practices
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Focuses on general-purpose Rust development, not specialized domains like embedded or WebAssembly
- Best practices continue to evolve with the Rust ecosystem
- Some recommendations may vary based on specific use cases and performance requirements
