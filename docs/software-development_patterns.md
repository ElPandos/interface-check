---
title:        Software Development Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Software Development Patterns

## Core Principles

### 1. SOLID Principles
The foundation of maintainable object-oriented design:
- **Single Responsibility**: Each class/module handles one concern only
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Many specific interfaces over one general-purpose
- **Dependency Inversion**: Depend on abstractions, not concretions

### 2. DRY (Don't Repeat Yourself)
Eliminate duplication through abstraction. Every piece of knowledge should have a single, authoritative representation in the system.

### 3. KISS (Keep It Simple, Stupid)
Prefer simple solutions over complex ones. Complexity is the enemy of maintainability.

### 4. YAGNI (You Aren't Gonna Need It)
Don't implement functionality until it's actually needed. Speculative generality creates dead code and maintenance burden.

### 5. Separation of Concerns
Divide systems into distinct sections, each addressing a separate concern. Business logic should be isolated from infrastructure.

## Essential Patterns

### Creational Patterns

**Factory Method**
- Creates objects without specifying exact class
- Use when: Object creation logic is complex or varies by context
- Implementation: Define interface for creation, let subclasses decide instantiation

**Builder**
- Constructs complex objects step-by-step
- Use when: Object has many optional parameters or complex construction
- Implementation: Separate construction from representation

**Singleton** (use sparingly)
- Ensures single instance with global access
- Use when: Exactly one instance needed (config, connection pools)
- Warning: Often overused; prefer dependency injection

### Structural Patterns

**Repository**
- Abstracts data access behind collection-like interface
- Use when: Decoupling domain from persistence layer
- Implementation: Interface defines operations, concrete class handles storage

**Adapter**
- Converts interface to one clients expect
- Use when: Integrating incompatible components
- Implementation: Wrapper translates between interfaces

**Decorator**
- Adds responsibilities dynamically without subclassing
- Use when: Extending behavior at runtime
- Implementation: Wrapper implements same interface, delegates to wrapped object

**Facade**
- Simplified interface to complex subsystem
- Use when: Hiding complexity from clients
- Implementation: Single entry point coordinating multiple components

### Behavioral Patterns

**Strategy**
- Defines family of interchangeable algorithms
- Use when: Multiple algorithms for same task, selected at runtime
- Implementation: Interface for algorithm, concrete implementations injected

**Observer**
- Automatic notification of state changes to dependents
- Use when: Event-driven systems, loose coupling between components
- Implementation: Subject maintains subscriber list, notifies on change

**Command**
- Encapsulates request as object
- Use when: Undo/redo, queuing, logging operations
- Implementation: Command interface with execute(), store parameters

### Architectural Patterns

**Hexagonal Architecture (Ports & Adapters)**
- Core business logic isolated from external systems
- Ports: Interfaces defining how core communicates
- Adapters: Implementations connecting to external systems
- Benefits: Technology-agnostic domain, easy testing, swappable infrastructure

**Clean Architecture**
- Dependency rule: Dependencies point inward toward domain
- Layers: Entities → Use Cases → Interface Adapters → Frameworks
- Domain code has no outward-facing dependencies

**Domain-Driven Design (DDD)**
- Model software to match business domain
- Bounded contexts with their own models
- Ubiquitous language shared between developers and domain experts
- Use when: Complex domains where model provides clear benefits

**Dependency Injection**
- Components receive dependencies rather than creating them
- Benefits: Testability, loose coupling, configuration flexibility
- Implementation: Constructor injection preferred over property/method injection

## Anti-Patterns to Avoid

### Code-Level Anti-Patterns

**Spaghetti Code**
- Symptoms: Tangled logic, no structure, excessive global state
- Fix: Extract methods, apply single responsibility, use meaningful names

**God Object/Class**
- Symptoms: One class knows/does everything, thousands of lines
- Fix: Split by responsibility, apply SOLID principles

**Copy-Paste Programming**
- Symptoms: Duplicated code blocks with minor variations
- Fix: Extract common logic, parameterize differences

**Magic Numbers/Strings**
- Symptoms: Hardcoded values without explanation
- Fix: Named constants, configuration, enums

**Error Hiding (Exception Swallowing)**
- Symptoms: Empty catch blocks, silent failures
- Fix: Log errors, propagate or handle meaningfully

### Architectural Anti-Patterns

**Big Ball of Mud**
- Symptoms: No discernible architecture, everything coupled
- Fix: Identify boundaries, introduce layers, refactor incrementally

**Golden Hammer**
- Symptoms: Using familiar tool for every problem regardless of fit
- Fix: Evaluate tools per problem, learn alternatives

**Lava Flow**
- Symptoms: Dead code nobody dares remove, unclear purpose
- Fix: Document decisions, remove unused code, version control

**Premature Optimization**
- Symptoms: Complex optimizations before measuring, unclear code
- Fix: Profile first, optimize bottlenecks, keep code readable

### Process Anti-Patterns

**Analysis Paralysis**
- Symptoms: Endless planning, fear of wrong decisions
- Fix: Time-box decisions, prototype, iterate

**Cargo Cult Programming**
- Symptoms: Using patterns/practices without understanding why
- Fix: Understand rationale, question assumptions

## Implementation Guidelines

### Starting a New Feature

1. **Understand the domain** - What problem are we solving?
2. **Define interfaces first** - How will components communicate?
3. **Start with the simplest implementation** - YAGNI applies
4. **Write tests alongside code** - Not after
5. **Refactor when patterns emerge** - Don't force patterns prematurely

### Applying Patterns

1. **Identify the problem** - What recurring issue are you facing?
2. **Match to pattern** - Which pattern addresses this problem?
3. **Evaluate trade-offs** - Is the complexity justified?
4. **Implement minimally** - Don't over-engineer
5. **Document the decision** - Why this pattern here?

### Refactoring Toward Patterns

1. **Ensure test coverage** - Safety net for changes
2. **Make small, incremental changes** - One refactoring at a time
3. **Verify behavior after each step** - Run tests frequently
4. **Extract, then abstract** - Concrete before generic

### Code Review Checklist

- [ ] Single responsibility per class/function?
- [ ] Dependencies injected, not created internally?
- [ ] No magic numbers or hardcoded strings?
- [ ] Error handling present and meaningful?
- [ ] No obvious duplication?
- [ ] Complexity justified by requirements?

## Success Metrics

### Code Quality Indicators

| Metric | Target | Warning |
|--------|--------|---------|
| Cyclomatic complexity | < 10 per function | > 15 |
| Class size | < 300 lines | > 500 lines |
| Function size | < 30 lines | > 50 lines |
| Test coverage | > 80% | < 60% |
| Duplication | < 3% | > 5% |

### Architectural Health

- **Coupling**: Low coupling between modules (measurable via dependency analysis)
- **Cohesion**: High cohesion within modules (related code together)
- **Dependency direction**: Dependencies flow toward stable abstractions
- **Change impact**: Changes localized to single module/layer

### Team Velocity Indicators

- **Time to understand**: New developers productive within reasonable timeframe
- **Change confidence**: Team comfortable making changes
- **Bug density**: Decreasing over time
- **Technical debt ratio**: Manageable, not growing unbounded

### Pattern Effectiveness

- Pattern solves the intended problem
- Code is more maintainable than without pattern
- Team understands and can extend the pattern
- No significant performance degradation

## Sources & References

- [Software Design Patterns - Jobsity](https://www.jobsity.com/blog/design-pattern-software) — GoF patterns overview and categories
- [Anti-Patterns to Avoid - Jalasoft](https://www.jalasoft.com/blog/anti-patterns-for-better-outcomes) — Common anti-patterns and their impact
- [SOLID, DRY, KISS, YAGNI Principles](https://scalastic.io/en/solid-dry-kiss/) — Core development principles
- [Clean Coding Principles - PullChecklist](https://www.pullchecklist.com/posts/clean-coding-principles) — Clean code practices
- [Hexagonal Architecture Guide - Scalastic](https://scalastic.io/en/hexagonal-architecture/) — Ports and adapters pattern
- [DDD and Hexagonal Architecture - Vaadin](https://vaadin.com/blog/ddd-part-3-domain-driven-design-and-the-hexagonal-architecture) — Domain-driven design integration
- [Repository Pattern with DI](https://exceptionnotfound.net/the-repository-service-pattern-with-dependency-injection-and-asp-net-core/) — Repository-service pattern implementation
- [God Object Anti-Pattern](https://linearb.io/blog/what-is-a-god-class) — God class identification and remediation
- [Golden Hammer Anti-Pattern](https://exceptionnotfound.net/the-golden-hammer-anti-pattern-primers/) — Tool overuse patterns
- [Architecture Patterns Guide - Substack](https://buildtolaunch.substack.com/p/architecture-patterns-complete-guide-to-architecture-decisions) — Architecture decision guidance

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
