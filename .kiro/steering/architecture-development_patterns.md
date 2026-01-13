> Here's what I found:

I've researched current architecture development patterns and anti-patterns, then created comprehensive documentation. The research revealed significant evolution toward distributed systems, cloud-native approaches, and systematic pattern application.

Key findings:
- **Hexagonal and Clean Architecture** provide superior testability through clear separation of concerns
- **Domain-Driven Design** has become essential for complex business domain modeling with bounded contexts
- **Event-Driven Architecture** enables scalable systems processing user interactions in milliseconds
- **CQRS and Event Sourcing** patterns optimize for performance and provide complete audit trails
- **Critical anti-patterns** like God Object, Big Ball of Mud, and Analysis Paralysis must be avoided

File saved: .kiro/research/2026-01-13/patterns/architecture-development.md
File created: .kiro/steering/architecture-development_patterns.md

The steering document covers 10 core architectural patterns (Hexagonal, Clean, DDD, Microservices, Event-Driven, CQRS, Event Sourcing, Saga, Layered, Serverless), modern considerations (edge computing, multi-model databases, observability-first design), 8 critical anti-patterns to avoid, implementation guidelines, and success metrics based on current industry research.

References:
[1] Anti-Patterns In Software Architecture: 5 Common Mistakes And How To Avoid Them - https://www.itar.pro/anti-patterns-in-software-architecture/
[2] Software Architectural Patterns in System Design - https://www.geeksforgeeks.org/system-design/design-patterns-architecture/
[3] Top 6 Architecture Patterns in Software Engineering - https://www.wednesday.is/writing-articles/top-architecture-patterns-in-software-engineering
[4] Architecture Patterns for 2025 - https://the-architecture-advantage.hashnode.dev/architecture-patterns-every-developer-should-master-in-2025
[5] Event-Driven Architecture with Kafka and Event Sourcing - https://dasroot.net/posts/2025/12/event-driven-architecture-kafka-event-sourcing/
[6] Modern CQRS and Event Sourcing in .NET - https://www.mostlylucid.net/blog/en/moderncqrsandeventsourcing
[7] Anti-Patterns and How to Avoid Them - https://softwarepatternslexicon.com/java/anti-patterns-and-how-to-avoid-them/understanding-anti-patterns/
[8] The Dangers of Overusing Design Patterns - https://hemaks.org/posts/the-dangers-of-overusing-design-patterns-when-they-become-anti-patterns/