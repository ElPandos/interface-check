---
title:        Rust Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Rust Best Practices

## Purpose
Establish standardized Rust development practices for safe, performant, and maintainable code leveraging Rust's unique strengths.

## Core Principles

### 1. Follow Upstream Guidelines
- **Rust API Guidelines**: Public interface design standards
- **Rust Style Guide**: Official formatting conventions
- **Rust Design Patterns**: Idiomatic code structures
- **Safety Standards**: Avoid undefined behavior patterns

### 2. Static Verification Tools
- **Clippy**: 800+ lints for bug prevention and code quality improvement
- **rustfmt**: Consistent source code formatting
- **Compiler Lints**: Additional warnings for better code quality
- **cargo-audit**: Security vulnerability scanning for dependencies
- **cargo-hack**: Validate all feature combinations work correctly
- **miri**: Unsafe code correctness validation

### 3. Comprehensive Lint Configuration
```toml
[lints.rust]
missing_debug_implementations = "warn"
unsafe_op_in_unsafe_fn = "warn"
unused_lifetimes = "warn"
redundant_lifetimes = "warn"
trivial_numeric_casts = "warn"

[lints.clippy]
cargo = { level = "warn", priority = -1 }
complexity = { level = "warn", priority = -1 }
correctness = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
perf = { level = "warn", priority = -1 }
style = { level = "warn", priority = -1 }
suspicious = { level = "warn", priority = -1 }

# Selected restriction lints for consistency
allow_attributes_without_reason = "warn"
undocumented_unsafe_blocks = "warn"
unnecessary_safety_comment = "warn"
```

### 4. Type Design Standards
- **Debug Implementation**: All public types must implement Debug
- **Display for User-Facing Types**: Types meant to be read implement Display
- **Common Traits**: Eagerly implement Copy, Clone, Eq, PartialEq, Ord, Hash, Default
- **Constructor Conventions**: Use static inherent methods (Foo::new())
- **Sensitive Data**: Custom Debug implementations that don't leak secrets

### 5. Code Organization
- **Smaller Crates**: Prefer multiple small crates over monolithic ones
- **Independent Modules**: Split functionality that can be used independently
- **Regular Functions**: Use regular functions over associated functions for general computation
- **Meaningful Names**: Avoid placeholder names like Service, Manager, Factory

## Error Handling Philosophy

### 1. Panic Guidelines
- **Panics Mean Stop**: Panics indicate program should terminate immediately
- **Not for Error Communication**: Use Result types for recoverable errors
- **Programming Bugs Only**: Panic for invariant violations and programming errors
- **Panic Safety**: Ensure code maintains consistent state after panic

### 2. Error Types
- **Result for Recoverable**: Use Result<T, E> for expected error conditions
- **Custom Error Types**: Implement std::error::Error for domain-specific errors
- **Error Propagation**: Use ? operator for clean error propagation
- **Context**: Provide meaningful error context and messages

## Documentation Standards

### 1. Code Documentation
- **Magic Numbers**: Document constants with rationale and side effects
- **Safety Comments**: All unsafe blocks must have safety documentation
- **API Documentation**: Comprehensive docs for public interfaces
- **Examples**: Include usage examples in documentation

### 2. Structured Logging
- **Message Templates**: Use structured logging with named properties
- **Event Naming**: Hierarchical dot-notation (component.operation.state)
- **Avoid Allocations**: Defer string formatting until viewing time
- **Sensitive Data**: Redact sensitive information in logs

## Performance Guidelines

### 1. Zero-Cost Abstractions
- **Idiomatic Code**: Write idiomatic Rust for compiler optimizations
- **Appropriate Data Structures**: Choose right collections for use case
- **Borrowing Over Cloning**: Prefer borrowing when ownership not needed
- **Profile Critical Paths**: Benchmark and profile performance-critical code

### 2. Memory Management
- **Ownership System**: Master Rust's ownership and borrowing
- **Lifetime Parameters**: Use lifetimes appropriately for references
- **Shared Ownership**: Use Rc/Arc only when necessary
- **Stack Allocation**: Prefer stack over heap allocation when possible

## Development Workflow

### 1. Tool Integration
```bash
# Format code
cargo fmt

# Run lints
cargo clippy

# Run tests
cargo test

# Check for security vulnerabilities
cargo audit

# Validate feature combinations
cargo hack check --feature-powerset
```

### 2. CI/CD Integration
- **Pre-commit Hooks**: Run formatting and linting before commits
- **Automated Testing**: Comprehensive test suite in CI pipeline
- **Security Scanning**: Regular dependency vulnerability checks
- **Documentation**: Generate and publish documentation automatically

## Advanced Patterns

### 1. Trait Design
- **Composable Interfaces**: Design traits for extensibility
- **Standard Traits**: Implement standard library traits consistently
- **Trait Objects**: Use dynamic dispatch judiciously
- **Associated Types**: Prefer associated types over generic parameters when appropriate

### 2. Unsafe Code Guidelines
- **Minimize Surface Area**: Keep unsafe code to absolute minimum
- **Safety Documentation**: Document all safety invariants
- **Safe Abstractions**: Provide safe wrappers over unsafe operations
- **Validation**: Use miri to validate unsafe code correctness

## Common Anti-Patterns to Avoid

### 1. Error Handling Issues
- Using `unwrap()` in production without justification
- Ignoring Result types with `let _ = ...`
- Panicking for recoverable errors
- Not providing error context

### 2. Code Quality Issues
- Ignoring compiler warnings and clippy suggestions
- Over-using unsafe code without documentation
- Creating overly complex type hierarchies
- Not implementing common traits for public types

### 3. Performance Issues
- Unnecessary cloning of large data structures
- String allocations in hot paths
- Inappropriate use of heap allocation
- Not leveraging zero-cost abstractions

## Quality Metrics

### 1. Code Quality Indicators
- **Clippy Warnings**: Track and minimize clippy warnings
- **Test Coverage**: Maintain high test coverage for critical code
- **Documentation Coverage**: Ensure public APIs are documented
- **Dependency Audit**: Regular security vulnerability scanning

### 2. Performance Metrics
- **Compile Times**: Monitor and optimize build performance
- **Runtime Performance**: Benchmark critical code paths
- **Memory Usage**: Profile memory allocation patterns
- **Binary Size**: Track executable size for deployment considerations

## Version History

- v1.0 (2026-01-12): Initial version based on Microsoft Rust Guidelines and community best practices
