---
title:        Rust Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Rust Best Practices

## Core Principles

1. **Embrace Ownership and Borrowing**: Rust's ownership system is not a constraint—it's a feature. Design APIs that work with the borrow checker, not against it. Prefer borrowing over cloning; prefer moving over borrowing when ownership transfer is semantically correct.

2. **Make Invalid States Unrepresentable**: Use Rust's type system (enums, newtypes, `Option`, `Result`) to encode invariants at compile time. If a state shouldn't exist, make it impossible to construct.

3. **Explicit Error Handling**: Never hide errors. Use `Result<T, E>` for fallible operations, `Option<T>` for optional values. Propagate errors with `?` and provide context. Reserve panics for unrecoverable programmer errors only.

4. **Zero-Cost Abstractions**: Write high-level, readable code knowing the compiler optimizes it to equivalent low-level code. Iterators, generics, and traits compile to the same machine code as hand-written loops.

5. **Leverage the Toolchain**: `cargo fmt`, `clippy`, and the compiler warnings are your first line of defense. Treat warnings as errors in CI. The compiler is your pair programmer.

## Essential Practices

### Error Handling

```rust
// Library code: Use thiserror for typed errors
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("failed to read config file: {0}")]
    Io(#[from] std::io::Error),
    #[error("invalid config format: {0}")]
    Parse(#[from] toml::de::Error),
}

// Application code: Use anyhow for ergonomic error handling
fn main() -> anyhow::Result<()> {
    let config = load_config()
        .context("failed to initialize application")?;
    Ok(())
}
```

**Guidelines:**
- Libraries: `thiserror` for custom error types consumers can match on
- Applications: `anyhow` for convenient error propagation with context
- Never use `unwrap()` in production code; use `expect()` only for invariants with clear messages
- Prefer `?` operator over explicit `match` for error propagation

### Ownership and Lifetimes

```rust
// Prefer borrowing over cloning
fn process(data: &str) -> Result<Output, Error> { ... }

// Use Cow for flexible ownership
fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))
    } else {
        Cow::Borrowed(input)
    }
}

// Explicit lifetime annotations when needed
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### Struct and Module Design

```rust
// Use the builder pattern for complex construction
#[derive(Debug, Clone)]
pub struct Config {
    timeout: Duration,
    retries: u32,
}

impl Config {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

// Prefer composition over large structs
pub struct Server {
    config: ServerConfig,
    state: ServerState,
    metrics: Metrics,
}
```

**Project Structure:**
```
my_project/
├── Cargo.toml
├── src/
│   ├── lib.rs          # Public API, re-exports
│   ├── config.rs       # Configuration types
│   ├── error.rs        # Error types
│   └── domain/
│       ├── mod.rs
│       └── models.rs
└── tests/
    └── integration.rs
```

### Async/Await with Tokio

```rust
// Prefer async for I/O-bound operations
async fn fetch_data(url: &str) -> Result<Response, Error> {
    let client = reqwest::Client::new();
    client.get(url).send().await?.error_for_status()
}

// Use tokio::spawn for concurrent tasks
async fn process_all(urls: Vec<String>) -> Vec<Result<Data, Error>> {
    let handles: Vec<_> = urls
        .into_iter()
        .map(|url| tokio::spawn(async move { fetch_data(&url).await }))
        .collect();
    
    futures::future::join_all(handles).await
}

// Avoid blocking in async contexts
// BAD: std::thread::sleep(Duration::from_secs(1));
// GOOD: tokio::time::sleep(Duration::from_secs(1)).await;
```

### Serialization with Serde

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiResponse {
    pub user_id: u64,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<Metadata>,
}
```

### Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_happy_path() {
        let result = process("valid input");
        assert!(result.is_ok());
    }

    #[test]
    fn test_edge_case_empty_input() {
        let result = process("");
        assert!(matches!(result, Err(Error::EmptyInput)));
    }

    #[test]
    #[should_panic(expected = "invariant violated")]
    fn test_invariant_violation() {
        violate_invariant();
    }
}

// Integration tests in tests/ directory
// Property-based testing with proptest for complex logic
```

### Tooling Configuration

```toml
# Cargo.toml
[lints.rust]
unsafe_code = "forbid"

[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
unwrap_used = "deny"
expect_used = "warn"
```

```bash
# CI pipeline essentials
cargo fmt --check
cargo clippy -- -D warnings
cargo test
cargo doc --no-deps
```

## Anti-Patterns to Avoid

### 1. Overusing `unwrap()` and `expect()`
```rust
// BAD: Panics on None/Err
let value = map.get("key").unwrap();

// GOOD: Handle the absence
let value = map.get("key").ok_or(Error::KeyNotFound)?;
```

### 2. Unnecessary Cloning
```rust
// BAD: Cloning when borrowing suffices
fn process(data: String) { ... }
process(my_string.clone());

// GOOD: Borrow instead
fn process(data: &str) { ... }
process(&my_string);
```

### 3. Ignoring Compiler Warnings
```rust
// BAD: Suppressing warnings without understanding
#[allow(unused)]

// GOOD: Fix the warning or document why it's acceptable
#[allow(dead_code)] // Used by external FFI
```

### 4. Overusing `Rc<RefCell<T>>` or `Arc<Mutex<T>>`
These indicate shared mutable state—often a design smell. Prefer:
- Message passing with channels
- Restructuring to avoid shared state
- Using interior mutability only when truly necessary

### 5. Stringly-Typed APIs
```rust
// BAD: Strings for everything
fn set_mode(mode: &str) { ... }

// GOOD: Enums for finite choices
enum Mode { Fast, Safe, Balanced }
fn set_mode(mode: Mode) { ... }
```

### 6. Macro Abuse
```rust
// BAD: Macro for simple logic
macro_rules! add { ($a:expr, $b:expr) => { $a + $b } }

// GOOD: Just use a function
fn add(a: i32, b: i32) -> i32 { a + b }
```

### 7. Monolithic Modules
Split large modules (>500 lines) into focused submodules. Each module should have a single responsibility.

### 8. Blocking in Async Code
```rust
// BAD: Blocks the async runtime
async fn bad() {
    std::thread::sleep(Duration::from_secs(1)); // Blocks!
}

// GOOD: Use async-aware primitives
async fn good() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}
```

### 9. Inadequate Error Context
```rust
// BAD: Lost context
file.read_to_string(&mut buf)?;

// GOOD: Add context
file.read_to_string(&mut buf)
    .with_context(|| format!("failed to read {}", path.display()))?;
```

## Implementation Guidelines

### Starting a New Project

1. **Initialize with best practices:**
   ```bash
   cargo new my_project
   cd my_project
   ```

2. **Configure lints in `Cargo.toml`:**
   ```toml
   [lints.clippy]
   all = "warn"
   pedantic = "warn"
   ```

3. **Set up pre-commit hooks:**
   ```bash
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: cargo-fmt
         name: cargo fmt
         entry: cargo fmt --
         language: system
         types: [rust]
       - id: cargo-clippy
         name: cargo clippy
         entry: cargo clippy -- -D warnings
         language: system
         types: [rust]
   ```

4. **Structure your crate:**
   - `src/lib.rs`: Public API surface
   - `src/error.rs`: Error types with `thiserror`
   - `src/config.rs`: Configuration structs with `serde`
   - Feature-specific modules as needed

### Code Review Checklist

- [ ] No `unwrap()` in non-test code
- [ ] All public items documented
- [ ] Error types provide actionable messages
- [ ] No unnecessary allocations or clones
- [ ] Clippy passes with no warnings
- [ ] Tests cover happy path and error cases
- [ ] Async code doesn't block

### Performance Optimization Order

1. **Measure first**: Use `criterion` for benchmarks
2. **Algorithm complexity**: O(n) beats O(n²) regardless of constants
3. **Reduce allocations**: Reuse buffers, use `&str` over `String`
4. **Use iterators**: They optimize to tight loops
5. **Profile**: `perf`, `flamegraph`, `cargo-instruments`
6. **Unsafe last**: Only after proving safe code is insufficient

## Success Metrics

### Code Quality
- **Clippy compliance**: Zero warnings with `pedantic` lint group
- **Test coverage**: >80% line coverage for business logic
- **Documentation**: All public APIs documented with examples

### Performance
- **Compile time**: Incremental builds under 10 seconds
- **Binary size**: Appropriate for deployment target
- **Runtime**: Meets latency/throughput requirements

### Maintainability
- **Module size**: No module exceeds 500 lines
- **Cyclomatic complexity**: Functions under 10
- **Dependency count**: Minimal, audited dependencies

### Safety
- **Unsafe blocks**: Zero or explicitly justified and audited
- **Panic paths**: Documented and tested
- **Error handling**: All errors propagated or explicitly handled

## Sources & References

- [Rust Best Practices - CursorRules](https://www.cursorrules.org/article/rust-cursor-mdc-file) — Comprehensive best practices guide covering code organization, patterns, and tooling (accessed 2026-01-14)
- [9 Rust Pitfalls Every Developer Should Know - Leapcell](https://leapcell.io/blog/nine-rust-pitfalls) — Common mistakes including unwrap overuse, ownership issues, and testing gaps (accessed 2026-01-14)
- [Rust Error Handling Best Practices 2025 - Toxigon](https://toxigon.com/rust-error-handling-best-practices) — Error handling with Result, Option, thiserror, and anyhow (accessed 2026-01-14)
- [Mastering Concurrency in Rust - Omid.dev](https://omid.dev/2024/06/15/mastering-concurrency-in-rust/) — Async/await patterns with Tokio (accessed 2026-01-14)
- [Clippy Lints - rust-lang.github.io](https://rust-lang.github.io/rust-clippy/master/index.html) — Official Clippy lint documentation (accessed 2026-01-14)
- [Zero-Cost Abstractions in Rust - DockYard](https://dockyard.com/blog/2025/04/15/zero-cost-abstractions-in-rust-power-without-the-price) — Understanding Rust's zero-cost abstraction philosophy (accessed 2026-01-14)
- [Using Serde in Rust - Shuttle](https://www.shuttle.dev/blog/2024/01/23/using-serde-rust) — Serialization best practices with serde (accessed 2026-01-14)
- [Cargo Workspaces - Earthly](https://earthly.dev/blog/cargo-workspace-crates/) — Project organization with workspaces (accessed 2026-01-14)
- [Idiomatic Rust - Ian Bull](https://www.ianbull.com/posts/idiomatic-rust) — What idiomatic Rust means in practice (accessed 2026-01-14)
- [Module and Crate Organization - Software Patterns Lexicon](https://softwarepatternslexicon.com/rust/idiomatic-rust-patterns/module-and-crate-organization-best-practices/) — Module structure best practices (accessed 2026-01-14)

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
