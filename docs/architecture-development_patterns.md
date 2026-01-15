---
title:        Architecture Development Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Architecture Development Patterns

## Core Principles

### 1. Separation of Concerns
Divide systems into distinct sections, each addressing a separate concern. Business logic should never depend on infrastructure details—databases, frameworks, and external services are implementation details that can be swapped.

### 2. Dependency Inversion
High-level modules must not depend on low-level modules; both should depend on abstractions. This inverts traditional layered dependencies, making core business logic independent of external systems.

### 3. Explicit Boundaries
Define clear boundaries between components using interfaces (ports) and implementations (adapters). Bounded contexts in DDD establish where specific models apply and how they interact.

### 4. Cohesion Over Coupling
Group code that changes together. Prefer high cohesion within components and loose coupling between them. Features that change for the same reason belong together.

### 5. Design for Change
Architecture should accommodate change without requiring rewrites. Isolate volatile components behind stable interfaces. Make the cost of change proportional to the scope of change.

## Essential Patterns

### Hexagonal Architecture (Ports & Adapters)

Separates business logic from external systems through ports (interfaces) and adapters (implementations).

**Structure:**
```
┌─────────────────────────────────────────┐
│              Adapters (Driving)          │
│   REST API │ CLI │ gRPC │ Message Queue │
├─────────────────────────────────────────┤
│              Ports (Inbound)             │
│         Use Case Interfaces              │
├─────────────────────────────────────────┤
│           Application Core               │
│    Domain Models │ Business Logic        │
├─────────────────────────────────────────┤
│              Ports (Outbound)            │
│      Repository │ Gateway Interfaces     │
├─────────────────────────────────────────┤
│              Adapters (Driven)           │
│   PostgreSQL │ Redis │ External APIs     │
└─────────────────────────────────────────┘
```

**When to use:** Complex domains requiring testability, systems needing technology flexibility, long-lived applications.

**Trade-offs:** More initial boilerplate, requires discipline to maintain boundaries.

### Clean Architecture

Concentric layers with dependencies pointing inward. Inner layers know nothing about outer layers.

**Layers (inside-out):**
1. **Entities** - Enterprise business rules, domain objects
2. **Use Cases** - Application-specific business rules
3. **Interface Adapters** - Controllers, presenters, gateways
4. **Frameworks & Drivers** - Web frameworks, databases, external tools

**Key rule:** Source code dependencies only point inward. Nothing in an inner circle can know about something in an outer circle.

### Vertical Slice Architecture

Organizes code by feature rather than technical layer. Each slice contains everything needed for one use case.

**Structure:**
```
features/
├── create_order/
│   ├── handler.py
│   ├── request.py
│   ├── response.py
│   ├── validator.py
│   └── repository.py
├── get_order/
│   ├── handler.py
│   ├── query.py
│   └── response.py
└── cancel_order/
    └── ...
```

**When to use:** CRUD-heavy applications, teams wanting feature isolation, rapid iteration environments.

**Trade-offs:** Potential code duplication across slices, harder to enforce cross-cutting concerns.

### Domain-Driven Design (DDD) Patterns

**Strategic Patterns:**
- **Bounded Context** - Explicit boundary where a domain model applies
- **Ubiquitous Language** - Shared vocabulary between developers and domain experts
- **Context Mapping** - Defines relationships between bounded contexts (Partnership, Customer/Supplier, Anticorruption Layer)

**Tactical Patterns:**
- **Aggregate** - Cluster of domain objects treated as a single unit for data changes
- **Entity** - Object with identity that persists over time
- **Value Object** - Immutable object defined by its attributes
- **Repository** - Abstraction for aggregate persistence
- **Domain Event** - Record of something significant that happened in the domain

### CQRS (Command Query Responsibility Segregation)

Separates read and write operations into different models.

**When to use:**
- Read and write workloads have different scaling requirements
- Complex domains where read models differ significantly from write models
- Event sourcing implementations
- Systems requiring audit trails

**Structure:**
```
Commands (Write)          Queries (Read)
     │                         │
     ▼                         ▼
Command Handler           Query Handler
     │                         │
     ▼                         ▼
Domain Model              Read Model
     │                         │
     ▼                         ▼
Write Database            Read Database
```

### Event Sourcing

Stores state as a sequence of events rather than current state.

**Benefits:**
- Complete audit trail
- Temporal queries (state at any point in time)
- Event replay for debugging or rebuilding projections
- Natural fit with CQRS

**Trade-offs:**
- Increased complexity
- Eventual consistency challenges
- Event schema evolution requires careful handling

## Anti-Patterns to Avoid

### Big Ball of Mud
**Symptom:** No discernible architecture; everything depends on everything.
**Cause:** Lack of boundaries, shortcuts under pressure, no architectural governance.
**Fix:** Establish bounded contexts, enforce dependency rules, refactor incrementally.

### Distributed Monolith
**Symptom:** Microservices that must be deployed together, share databases, or have synchronous dependencies.
**Cause:** Splitting by technical layer instead of business capability, shared data ownership.
**Fix:** Define clear service boundaries around business capabilities, embrace eventual consistency.

### Anemic Domain Model
**Symptom:** Domain objects are data containers with getters/setters; all logic lives in services.
**Cause:** Procedural thinking, over-reliance on transaction scripts.
**Fix:** Push behavior into domain objects, use rich domain models with encapsulated state.

### Leaky Abstractions
**Symptom:** Infrastructure details leak into business logic (SQL in use cases, HTTP status codes in domain).
**Cause:** Missing or poorly designed ports/interfaces.
**Fix:** Define clean interfaces at boundaries, use adapters to translate between layers.

### Premature Microservices
**Symptom:** Starting with microservices before understanding domain boundaries.
**Cause:** Hype-driven development, assuming scale requirements.
**Fix:** Start with a well-structured monolith, extract services when boundaries are clear and scale demands it.

### Analysis Paralysis
**Symptom:** Endless architectural discussions without decisions or implementation.
**Cause:** Fear of wrong decisions, lack of decision-making framework.
**Fix:** Make decisions at the "last responsible moment," document decisions in ADRs, accept that some decisions are reversible.

### Golden Hammer
**Symptom:** Applying the same architecture pattern to every problem.
**Cause:** Familiarity bias, lack of pattern knowledge.
**Fix:** Match patterns to problem characteristics, evaluate trade-offs for each context.

### Cargo Cult Architecture
**Symptom:** Adopting patterns because "Netflix/Google does it" without understanding why.
**Cause:** Copying solutions without understanding the problems they solve.
**Fix:** Understand your actual requirements, scale, and constraints before adopting patterns.

## Implementation Guidelines

### Step 1: Understand the Domain
- Collaborate with domain experts
- Identify core domain vs supporting/generic subdomains
- Establish ubiquitous language
- Map bounded contexts and their relationships

### Step 2: Choose Appropriate Patterns
| Characteristic | Recommended Pattern |
|----------------|---------------------|
| Complex business rules | DDD + Hexagonal |
| CRUD-dominant | Vertical Slices |
| Different read/write scaling | CQRS |
| Audit requirements | Event Sourcing |
| Multiple UIs/channels | Hexagonal/Clean |
| Rapid feature iteration | Vertical Slices |

### Step 3: Define Boundaries
- Establish module/package structure reflecting architecture
- Define interfaces (ports) at boundaries
- Create adapters for external dependencies
- Enforce dependency rules (linting, architecture tests)

### Step 4: Implement Incrementally
```python
# Example: Hexagonal structure in Python
src/
├── domain/           # Core business logic (no external deps)
│   ├── models/
│   ├── services/
│   └── events/
├── application/      # Use cases, orchestration
│   ├── commands/
│   ├── queries/
│   └── ports/        # Interfaces for driven adapters
├── adapters/
│   ├── inbound/      # REST, CLI, gRPC
│   └── outbound/     # Database, external APIs
└── infrastructure/   # Framework configuration, DI
```

### Step 5: Validate Architecture
- Write architecture tests (ArchUnit, import-linter)
- Review dependency graphs regularly
- Measure coupling metrics
- Conduct architecture decision reviews

### Step 6: Document Decisions
Use Architecture Decision Records (ADRs):
```markdown
# ADR-001: Use Hexagonal Architecture

## Status
Accepted

## Context
We need to support multiple interfaces (REST, CLI, message queue) 
and swap databases without affecting business logic.

## Decision
Adopt hexagonal architecture with explicit ports and adapters.

## Consequences
- Increased initial setup time
- Better testability (mock adapters)
- Technology flexibility
```

## Success Metrics

### Structural Metrics
- **Coupling:** Measure afferent/efferent coupling between modules
- **Dependency violations:** Count of dependencies breaking architectural rules
- **Cyclic dependencies:** Should be zero between bounded contexts
- **Instability index:** Ratio of efferent to total coupling (Ce / (Ca + Ce))

### Change Metrics
- **Change locality:** Percentage of changes contained within single module/slice
- **Deployment independence:** Can components be deployed independently?
- **Test isolation:** Can components be tested without spinning up entire system?

### Quality Metrics
- **Time to implement feature:** Should decrease or remain stable as system grows
- **Defect locality:** Bugs should be isolated to specific components
- **Onboarding time:** New developers should understand structure quickly

### Operational Metrics
- **Build time:** Modular architecture enables parallel builds
- **Test execution time:** Isolated tests run faster
- **Deployment frequency:** Good architecture enables frequent, safe deployments

### Review Checklist
- [ ] Dependencies flow inward (toward domain)
- [ ] No framework imports in domain layer
- [ ] Interfaces defined at boundaries
- [ ] Each bounded context has clear ownership
- [ ] Architecture tests pass in CI
- [ ] ADRs document significant decisions

## Sources & References

- [Hexagonal Architecture - Ports and Adapters Pattern](https://miladezzat.medium.com/hexagonal-architecture-ports-and-adapters-pattern-5ad2421802ec) — Core hexagonal concepts and implementation
- [Hexagonal Architecture – What Is It? Why Use It?](https://www.happycoders.eu/software-craftsmanship/hexagonal-architecture/) — Detailed explanation of ports and adapters
- [From Hexagonal to Clean Architecture](https://codeartify.substack.com/p/from-hexagonal-to-clean-architecture) — Comparison and evolution of layered patterns
- [Complete Guide to Architecture Decisions](https://buildtolaunch.substack.com/p/architecture-patterns-complete-guide-to-architecture-decisions) — Decision frameworks and pattern selection
- [Vertical Slice Architecture](https://www.milanjovanovic.tech/blog/vertical-slice-architecture-structuring-vertical-slices) — Feature-based organization patterns
- [Mastering Bounded Contexts and Aggregate Roots](https://leapcell.io/blog/mastering-bounded-contexts-and-aggregate-roots-in-backend-development) — DDD tactical patterns
- [Event Sourcing and CQRS in Depth](https://softwarepatternslexicon.com/microservices/advanced-topics-in-microservices/event-sourcing-and-cqrs-in-depth/) — Advanced data patterns
- [Layered Architecture, Dependency Injection, and Dependency Inversion](https://www.codemag.com/article/0705071/Layered-Architecture-Dependency-Injection-and-Dependency-Inversion) — SOLID principles in architecture
- [Why Starting with Microservices Can Be Your Biggest Mistake](https://designgurus.substack.com/p/why-starting-with-microservices-can) — Monolith-first approach
- [Domain-Driven Design (Wikipedia)](https://en.wikipedia.org/wiki/Domain-driven_design) — DDD overview and context mapping patterns

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
