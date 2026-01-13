> Here's what I found:

I've researched current threading patterns and anti-patterns, revealing significant evolution toward prevention-focused approaches and systematic anti-pattern recognition. The research shows critical insights into modern concurrent programming practices.

Key findings:
- **Prevention over detection** emphasizes designing out problems rather than detecting them later through immutable data structures and minimal shared state
- **False sharing impact** can cause 10-20x performance degradation when multiple threads access different variables in the same cache line
- **Lock ordering** is critical - establishing global lock acquisition order prevents deadlock scenarios
- **Resource management** anti-patterns like thread creation overhead and exception swallowing remain common issues
- **Modern concurrency evolution** includes structured concurrency, async/await patterns, and virtual threads

File saved: .kiro/research/2026-01-13/patterns/threading.md
File created: .kiro/steering/threading_patterns.md

The steering document covers 5 core patterns (producer-consumer, thread pool, monitor, actor model, lock-free programming), 5 critical anti-pattern categories (shared state, locking, resource management, performance, design), implementation guidelines emphasizing prevention-focused design, and success metrics based on current industry research.

References:
[1] Race Conditions, Deadlocks, and Producer-Consumer - https://designgurus.substack.com/p/mastering-multithreading-patterns
[2] The Silent Killer of Multi-Threaded Performance: False Sharing - https://bytegoblin.io/blog/the-silent-killer-of-multi-threaded-performance-false-sharing.mdx
[3] Avoiding Deadlocks: Essential Concurrency Design Patterns - https://www.javanexus.com/blog/avoiding-deadlocks-concurrency-patterns
[4] Python: Guide to structured concurrency - https://applifting.io/blog/python-structured-concurrency
[5] Concurrency Flavours - https://isocpp.org/blog/2025/12/concurrency-flavours-lucian-radu-teodorescu