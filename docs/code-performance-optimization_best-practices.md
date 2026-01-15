---
title:        Code Performance Optimization Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Code Performance Optimization Best Practices

## Core Principles

### 1. Measure First, Optimize Second
Never optimize without profiling data. Premature optimization leads to complex, unmaintainable code that often doesn't address actual bottlenecks. Use profilers to identify the critical 20% of code consuming 80% of resources.

### 2. Algorithmic Complexity Trumps Micro-Optimizations
Reducing O(n²) to O(n log n) yields far greater gains than any micro-optimization. Always analyze Big O complexity before optimizing implementation details. A better algorithm beats a faster implementation of a slow algorithm.

### 3. Optimize for the Common Case
Focus optimization efforts on hot paths—code executed frequently under typical workloads. Edge cases and rarely-executed branches rarely justify optimization investment.

### 4. Trade-offs Are Explicit
Every optimization has costs: memory vs. speed, readability vs. performance, development time vs. runtime. Document trade-offs explicitly and ensure they align with actual requirements.

### 5. Performance Is a Feature
Treat performance requirements like functional requirements—define targets, measure continuously, and prevent regressions through automated testing.

## Essential Practices

### Profiling Strategy

**Tool Selection by Use Case:**
- **cProfile**: Built-in deterministic profiler for function-level CPU analysis
- **py-spy**: Low-overhead sampling profiler safe for production use
- **Scalene**: Combined CPU, GPU, and memory profiler with line-level granularity
- **memory_profiler**: Dedicated memory usage tracking and leak detection
- **Pyinstrument**: Statistical profiler with readable call stack visualization

**Profiling Workflow:**
```python
# Quick profiling with cProfile
python -m cProfile -s cumtime script.py

# Production-safe sampling with py-spy
py-spy record -o profile.svg -- python script.py

# Line-level analysis with Scalene
scalene script.py
```

**Key Metrics to Track:**
- Wall-clock time (user-perceived latency)
- CPU time (actual computation)
- Memory allocation rate and peak usage
- I/O wait time
- Cache hit/miss ratios

### Data Structure Selection

**Choose structures matching access patterns:**

| Operation | List | Set | Dict | deque |
|-----------|------|-----|------|-------|
| Append | O(1)* | - | - | O(1) |
| Prepend | O(n) | - | - | O(1) |
| Lookup | O(n) | O(1) | O(1) | O(n) |
| Membership | O(n) | O(1) | O(1) | O(n) |
| Delete by value | O(n) | O(1) | O(1) | O(n) |

*Amortized

**Practical Guidelines:**
- Use `set` for membership tests, not lists
- Use `dict` for key-value lookups, not linear search
- Use `collections.deque` for queue operations
- Use `__slots__` on frequently instantiated classes to reduce memory
- Prefer generators over lists for large sequences processed once

### Caching and Memoization

**Built-in Caching:**
```python
from functools import lru_cache, cache

@lru_cache(maxsize=128)  # Bounded LRU cache
def expensive_computation(x: int) -> int:
    return x ** 2

@cache  # Unbounded cache (Python 3.9+)
def pure_function(x: int) -> int:
    return x * 2
```

**Cache Sizing Strategy:**
- Start with `maxsize=128` and adjust based on hit rate
- Monitor cache statistics: `func.cache_info()`
- Clear caches when underlying data changes: `func.cache_clear()`
- Consider TTL-based caching for time-sensitive data

**When to Cache:**
- Pure functions with expensive computation
- Repeated calls with same arguments
- I/O-bound operations (API calls, database queries)

**When NOT to Cache:**
- Functions with side effects
- Large return values that consume excessive memory
- Rapidly changing underlying data

### Concurrency and Parallelism

**Python Concurrency Model:**

| Approach | Best For | GIL Impact |
|----------|----------|------------|
| `asyncio` | I/O-bound (network, disk) | Cooperative, single-threaded |
| `threading` | I/O-bound with blocking calls | Limited by GIL for CPU work |
| `multiprocessing` | CPU-bound computation | Bypasses GIL via separate processes |
| `concurrent.futures` | Simple parallel execution | Abstraction over threads/processes |

**Decision Framework:**
```
Is the task I/O-bound?
├── Yes → Use asyncio or threading
│   └── Many concurrent connections? → asyncio
│   └── Blocking I/O libraries? → threading
└── No (CPU-bound) → Use multiprocessing
    └── Need shared state? → Consider ProcessPoolExecutor with careful design
```

**Python 3.13+ Free-Threading:**
- Experimental GIL-free mode available
- Enable with `PYTHON_GIL=0` environment variable
- Allows true thread parallelism for CPU-bound work
- Requires thread-safe code design

### Database Query Optimization

**N+1 Query Problem:**
```python
# BAD: N+1 queries
for user in users:
    print(user.profile.bio)  # Separate query per user

# GOOD: Eager loading
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # Single query
```

**Indexing Strategy:**
- Index columns used in WHERE, JOIN, and ORDER BY clauses
- Use composite indexes for multi-column queries
- Avoid over-indexing (slows writes, consumes storage)
- Analyze query plans with EXPLAIN

**Query Optimization Checklist:**
1. Select only needed columns, not `SELECT *`
2. Use pagination for large result sets (keyset pagination > offset)
3. Batch inserts/updates instead of individual operations
4. Use connection pooling
5. Cache frequently-accessed, rarely-changed data

### Memory Optimization

**Reduce Allocation Overhead:**
```python
# Use __slots__ for memory-efficient classes
class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Use generators for large sequences
def process_large_file(path: str):
    with open(path) as f:
        for line in f:  # Lazy iteration
            yield process_line(line)
```

**Memory Profiling:**
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    data = [i ** 2 for i in range(1000000)]
    return sum(data)
```

**Common Memory Issues:**
- Unbounded caches growing indefinitely
- Circular references preventing garbage collection
- Large objects held in closures
- String concatenation in loops (use `str.join()`)

### I/O Optimization

**File Operations:**
- Use buffered I/O (default in Python)
- Process files in chunks for large files
- Use `mmap` for random access to large files
- Prefer binary mode for non-text data

**Network Operations:**
- Use connection pooling and keep-alive
- Implement request batching where possible
- Use compression for large payloads
- Set appropriate timeouts

## Anti-Patterns to Avoid

### 1. Premature Optimization
Optimizing code before profiling identifies actual bottlenecks. Results in complex, hard-to-maintain code that often doesn't improve real-world performance.

**Instead:** Write clear, correct code first. Profile under realistic conditions. Optimize only proven bottlenecks.

### 2. Optimizing the Wrong Layer
Micro-optimizing Python loops when the bottleneck is database queries or network latency.

**Instead:** Profile end-to-end. Identify which layer (CPU, I/O, network, database) dominates latency.

### 3. Ignoring Algorithmic Complexity
Using O(n²) algorithms when O(n log n) alternatives exist, then trying to optimize the implementation.

**Instead:** Analyze complexity first. Choose appropriate algorithms and data structures before implementation.

### 4. Unbounded Caching
Caching without size limits, leading to memory exhaustion.

**Instead:** Always set `maxsize` on caches. Monitor memory usage. Implement eviction policies.

### 5. Synchronous I/O in Hot Paths
Blocking on I/O operations in performance-critical code paths.

**Instead:** Use async I/O, background workers, or pre-fetching for I/O in hot paths.

### 6. Over-Parallelization
Creating more threads/processes than available cores, leading to context-switching overhead.

**Instead:** Match parallelism to available resources. Use thread/process pools with appropriate sizing.

### 7. Ignoring Memory Allocation
Creating many short-lived objects in tight loops, causing GC pressure.

**Instead:** Reuse objects where possible. Use object pools for frequently allocated types. Pre-allocate collections with known sizes.

### 8. String Concatenation in Loops
```python
# BAD: O(n²) due to string immutability
result = ""
for item in items:
    result += str(item)

# GOOD: O(n)
result = "".join(str(item) for item in items)
```

## Implementation Guidelines

### Step 1: Establish Baseline
1. Define performance requirements (latency targets, throughput goals)
2. Create representative benchmarks reflecting real workloads
3. Measure current performance under realistic conditions
4. Document baseline metrics

### Step 2: Profile and Identify Bottlenecks
1. Run profiler under realistic load
2. Identify hot paths (functions consuming most time)
3. Distinguish CPU-bound vs. I/O-bound bottlenecks
4. Analyze memory allocation patterns

### Step 3: Prioritize Optimizations
1. Rank bottlenecks by impact (time × frequency)
2. Estimate effort vs. benefit for each optimization
3. Consider maintainability impact
4. Start with highest-impact, lowest-effort changes

### Step 4: Implement and Validate
1. Make one change at a time
2. Re-measure after each change
3. Verify correctness (optimization bugs are common)
4. Document the optimization and its rationale

### Step 5: Prevent Regressions
1. Add performance tests to CI/CD pipeline
2. Set alerting thresholds for key metrics
3. Review performance impact in code reviews
4. Maintain performance documentation

### Performance Testing Pattern
```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.4f}s")

# Usage
with timer("database_query"):
    results = execute_query()
```

## Success Metrics

### Latency Metrics
- **P50 (median)**: Typical user experience
- **P95**: Experience for most users
- **P99**: Worst-case for nearly all users
- **P99.9**: Tail latency (critical for high-traffic systems)

### Throughput Metrics
- Requests per second (RPS)
- Transactions per second (TPS)
- Operations per second for batch processing

### Resource Utilization
- CPU utilization (target: 60-80% under normal load)
- Memory usage and allocation rate
- I/O wait time
- Network bandwidth utilization

### Application-Specific Metrics
- Page load time (web applications)
- Time to first byte (TTFB)
- Import time (libraries/packages)
- Cold start time (serverless functions)

### Monitoring Best Practices
- Track metrics over time, not just point-in-time
- Set up alerting for degradation
- Compare against baselines after deployments
- Use percentiles, not averages, for latency

### Performance Budget Example
```
API Response Time:
- P50: < 100ms
- P95: < 500ms
- P99: < 1000ms

Memory Usage:
- Peak: < 512MB
- Steady state: < 256MB

Startup Time:
- Cold start: < 2s
- Warm start: < 500ms
```

## Sources & References

[Python Package Performance Profiling Guide](https://mer.vin/2026/01/python-package-performance-profiling-guide/) — Practical techniques for identifying and fixing performance bottlenecks in Python packages. Accessed 2026-01-14.

[Django Performance and Optimization](https://docs.djangoproject.com/en/5.1/topics/performance/) — Official Django documentation on performance optimization techniques. Accessed 2026-01-14.

[Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/) — End-to-end software performance fundamentals covering latency, throughput, and percentiles. Accessed 2026-01-14.

[Top 7 Python Profiling Tools](https://daily.dev/blog/top-7-python-profiling-tools-for-performance) — Comparison of Python profiling tools including py-spy, Scalene, and memory_profiler. Accessed 2026-01-14.

[Scalene GitHub Repository](https://github.com/plasma-umass/scalene) — High-performance CPU, GPU, and memory profiler for Python. Accessed 2026-01-14.

[Data Structures and Algorithm Complexity](https://codecake.ai/blog/data-structures-and-algorithm-complexity/) — Guide on algorithmic complexity and data structure selection. Accessed 2026-01-14.

[Speed up Python with lru_cache](https://www.infoworld.com/article/2262345/speed-up-python-functions-with-memoization-and-lrucache.html) — Practical guide to memoization and caching in Python. Accessed 2026-01-14.

[Performance Optimization Standards](https://www.codingrules.ai/rules/performance-optimization-standards-for-architecture) — Guidelines for application performance and architecture optimization. Accessed 2026-01-14.

[Concurrency in Python](https://norbix.dev/posts/concurrency-in-python/) — Overview of Python concurrency models including asyncio, threading, and multiprocessing. Accessed 2026-01-14.

[Premature Optimization Anti-Pattern](https://www.minware.com/guide/anti-patterns/premature-optimization) — Analysis of premature optimization as an anti-pattern. Accessed 2026-01-14.

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
