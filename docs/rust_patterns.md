---
title:        Rust Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Rust Patterns

## Core Principles

1. **Ownership-First Design**: Structure code around Rust's ownership model. Every value has exactly one owner; borrowing enables temporary access without transfer. Design APIs that make ownership semantics explicit and intuitive.

2. **Zero-Cost Abstractions**: Leverage traits, generics, and iterators that compile to efficient machine code. High-level patterns should not impose runtime overhead compared to hand-written low-level code.

3. **Explicit Error Handling**: Use `Result<T, E>` for recoverable errors and `Option<T>` for optional values. Make failure modes visible in type signatures. Reserve `panic!` for unrecoverable programmer errors only.

4. **Type-Driven Development**: Encode invariants in the type system. Use newtypes, enums, and the typestate pattern to make illegal states unrepresentable at compile time.

5. **Fearless Concurrency**: Rust's ownership rules prevent data races at compile time. Use `Arc<Mutex<T>>`, channels, or async/await patterns knowing the compiler enforces thread safety.

## Essential Patterns

### Builder Pattern
Construct complex objects step-by-step with compile-time validation:

```rust
#[derive(Default)]
pub struct Config {
    host: String,
    port: u16,
    timeout_ms: u64,
}

impl Config {
    pub fn new() -> Self { Self::default() }
    
    pub fn host(mut self, host: impl Into<String>) -> Self {
        self.host = host.into();
        self
    }
    
    pub fn port(mut self, port: u16) -> Self {
        self.port = port;
        self
    }
    
    pub fn build(self) -> Result<Server, ConfigError> {
        // Validate and construct
        Ok(Server { config: self })
    }
}

// Usage: Config::new().host("localhost").port(8080).build()?
```

### Newtype Pattern
Wrap primitive types for type safety and semantic clarity:

```rust
pub struct UserId(u64);
pub struct OrderId(u64);

// Compiler prevents mixing UserId with OrderId
fn get_user_orders(user: UserId) -> Vec<OrderId> { /* ... */ }
```

### Typestate Pattern
Encode state transitions in the type system:

```rust
pub struct Connection<S> { state: S }
pub struct Disconnected;
pub struct Connected;

impl Connection<Disconnected> {
    pub fn connect(self) -> Result<Connection<Connected>, Error> { /* ... */ }
}

impl Connection<Connected> {
    pub fn send(&self, data: &[u8]) -> Result<(), Error> { /* ... */ }
    pub fn disconnect(self) -> Connection<Disconnected> { /* ... */ }
}

// Compile error: cannot call send() on Disconnected
```

### Iterator Combinators
Chain operations for expressive, zero-cost data processing:

```rust
let result: Vec<_> = items
    .iter()
    .filter(|x| x.is_valid())
    .map(|x| x.transform())
    .take(10)
    .collect();
```

### Error Propagation with `?`
Clean error handling with automatic conversion:

```rust
fn process_file(path: &Path) -> Result<Data, AppError> {
    let content = std::fs::read_to_string(path)?;  // io::Error -> AppError
    let parsed = serde_json::from_str(&content)?;  // serde::Error -> AppError
    Ok(parsed)
}
```

### RAII and Drop
Resource cleanup via destructors:

```rust
pub struct TempFile(PathBuf);

impl Drop for TempFile {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}
```

### Interior Mutability
Controlled mutation through shared references:

```rust
use std::cell::RefCell;
use std::rc::Rc;

// Single-threaded shared mutable state
let shared = Rc::new(RefCell::new(vec![]));
shared.borrow_mut().push(42);

// Thread-safe variant
use std::sync::{Arc, Mutex};
let shared = Arc::new(Mutex::new(vec![]));
shared.lock().unwrap().push(42);
```

## Anti-Patterns to Avoid

### 1. Overusing `unsafe`
**Problem**: Bypassing Rust's safety guarantees unnecessarily.
**Solution**: Use safe abstractions. When `unsafe` is required, isolate it in small, well-documented modules with safe public APIs.

### 2. Excessive `.unwrap()` / `.expect()`
**Problem**: Runtime panics instead of proper error handling.
**Solution**: Use `?` operator, `match`, or combinators (`map`, `and_then`, `unwrap_or_else`).

```rust
// Bad
let value = map.get("key").unwrap();

// Good
let value = map.get("key").ok_or(KeyNotFound)?;
```

### 3. Fighting the Borrow Checker
**Problem**: Complex lifetime annotations, excessive `Rc<RefCell<T>>`, or cloning everything.
**Solution**: Restructure code to work with ownership. Often indicates architectural issues.

### 4. Blocking in Async Code
**Problem**: Using `std::thread::sleep` or synchronous I/O in async functions.
**Solution**: Use async equivalents (`tokio::time::sleep`, async I/O).

```rust
// Bad
async fn fetch() {
    std::thread::sleep(Duration::from_secs(1)); // Blocks executor
}

// Good
async fn fetch() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}
```

### 5. Stringly-Typed APIs
**Problem**: Using `String` where enums or newtypes provide compile-time safety.
**Solution**: Define domain types.

```rust
// Bad
fn set_status(status: &str) { /* ... */ }

// Good
enum Status { Pending, Active, Completed }
fn set_status(status: Status) { /* ... */ }
```

### 6. Premature Optimization
**Problem**: Micro-optimizing before profiling, sacrificing readability.
**Solution**: Write clear code first. Profile with `cargo flamegraph` or `perf`. Optimize hot paths only.

### 7. Monolithic Crates
**Problem**: Single massive crate with slow compilation and poor modularity.
**Solution**: Split into workspace with focused crates. Use `pub(crate)` for internal APIs.

### 8. Ignoring Clippy Warnings
**Problem**: Missing idiomatic improvements and potential bugs.
**Solution**: Run `cargo clippy` regularly. Configure `#![warn(clippy::pedantic)]` for stricter checks.

### 9. Clone-Happy Code
**Problem**: Cloning to avoid borrow checker instead of proper ownership design.
**Solution**: Use references where possible. Clone only when semantically appropriate.

### 10. Misusing `Arc<Mutex<T>>` Everywhere
**Problem**: Treating Rust like a GC language with shared mutable state.
**Solution**: Prefer message passing (channels), or restructure to reduce shared state.

## Implementation Guidelines

### Project Setup
1. Use `cargo new --lib` or `cargo new --bin`
2. Configure `Cargo.toml` with appropriate edition (2021+)
3. Set up CI with `cargo fmt --check`, `cargo clippy`, `cargo test`
4. Add `rust-toolchain.toml` for reproducible builds

### Code Organization
```
src/
├── lib.rs          # Public API, re-exports
├── error.rs        # Custom error types
├── types.rs        # Domain types, newtypes
├── config.rs       # Configuration handling
└── internal/       # Private implementation
    └── mod.rs
```

### Error Handling Strategy
1. Define crate-level error enum with `thiserror`
2. Implement `From` for underlying errors
3. Use `?` for propagation
4. Provide context with `anyhow` in applications

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Parse error: {0}")]
    Parse(#[from] serde_json::Error),
    #[error("Invalid state: {0}")]
    InvalidState(String),
}
```

### Testing Approach
1. Unit tests in same file with `#[cfg(test)]` module
2. Integration tests in `tests/` directory
3. Use `proptest` or `quickcheck` for property-based testing
4. Benchmark with `criterion`

### Documentation
1. Document public items with `///` doc comments
2. Include examples that compile (`cargo test` runs doc tests)
3. Use `#![deny(missing_docs)]` to enforce documentation

## Success Metrics

### Code Quality
- **Zero Clippy warnings** on pedantic level
- **100% public API documentation** coverage
- **No `unsafe` blocks** outside designated modules
- **< 5% `.unwrap()` usage** (prefer `?` or explicit handling)

### Performance
- **Compile time** under 30s for incremental builds
- **Binary size** appropriate for deployment target
- **Memory usage** validated with `valgrind` or `heaptrack`
- **Benchmarks** tracked over time with `criterion`

### Maintainability
- **Cyclomatic complexity** < 10 per function
- **Module coupling** minimized (clear dependency graph)
- **Test coverage** > 80% for critical paths
- **Breaking changes** documented in CHANGELOG

### Safety
- **No panics** in library code (return `Result`)
- **Fuzz testing** for parsers and untrusted input
- **MIRI** clean for unsafe code (`cargo +nightly miri test`)
- **Audit dependencies** with `cargo audit`

## Sources & References

- [Software Patterns Lexicon - Rust Anti-Patterns](https://softwarepatternslexicon.com/rust/anti-patterns-and-common-pitfalls/recognizing-anti-patterns-in-rust/) — Comprehensive anti-pattern catalog accessed 2026-01-14
- [Compile N Run - Rust Idiomatic Code](https://www.compilenrun.com/docs/language/rust/rust-best-practices/rust-idiomatic-code) — Idiomatic patterns and naming conventions accessed 2026-01-14
- [Zero to Mastery - Typestate Pattern](https://zerotomastery.io/blog/rust-typestate-patterns/) — Typestate pattern implementation accessed 2026-01-14
- [Software Patterns Lexicon - Rust Design Patterns](https://softwarepatternslexicon.com/patterns-rust/) — Comprehensive pattern reference accessed 2026-01-14
- [Microsoft Rust Guidelines](https://microsoft.github.io/rust-guidelines/guidelines/checklist/index.html) — Pragmatic Rust guidelines accessed 2026-01-14
- [Rust Unofficial Patterns](https://rust-unofficial.github.io/patterns/) — Community pattern collection accessed 2026-01-14
- [Effective Rust](https://www.lurklurk.org/effective-rust/) — Best practices guide accessed 2026-01-14

## Version History
- v1.0 (2026-01-14 00:00:00): Initial version
