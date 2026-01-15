---
title:        Code Performance Optimization Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Code Performance Optimization Patterns

## Core Principles

1. **Measure Before Optimizing**: Profile first, optimize second. Premature optimization wastes effort on non-bottlenecks. Use profilers (cProfile, py-spy, perf) to identify actual hotspots.

2. **Algorithmic Complexity Trumps Micro-Optimization**: O(n²) → O(n log n) beats any micro-optimization. Fix algorithmic issues before tweaking constants.

3. **Memory Access Patterns Matter**: Cache locality dominates modern performance. Sequential access beats random access by 10-100x. Data layout affects speed more than clever code.

4. **I/O is the Bottleneck**: Network and disk I/O are orders of magnitude slower than CPU. Batch operations, use async I/O, minimize round-trips.

5. **Simplicity Enables Optimization**: Simple code is easier to optimize and often faster. Compilers/interpreters optimize predictable patterns better.

## Essential Patterns

### Data Structure Selection

```python
# Pattern: Choose appropriate data structures for access patterns

# O(1) membership testing - use set, not list
valid_ids: set[str] = {"a", "b", "c"}  # Good
# valid_ids: list[str] = ["a", "b", "c"]  # Bad: O(n) lookup

# O(1) key-value access - use dict
cache: dict[str, Result] = {}

# Ordered unique elements - use dict (Python 3.7+)
seen: dict[str, None] = {}  # Preserves insertion order

# Counting - use Counter
from collections import Counter
counts = Counter(items)  # Not manual dict incrementing
```

### Lazy Evaluation and Generators

```python
# Pattern: Process data lazily to reduce memory and enable early termination

# Generator for large datasets
def process_large_file(path: Path) -> Iterator[Record]:
    with path.open() as f:
        for line in f:  # Lazy line reading
            yield parse_record(line)

# Generator expressions over list comprehensions for single-pass
total = sum(x.value for x in items)  # Good: O(1) memory
# total = sum([x.value for x in items])  # Bad: O(n) memory

# itertools for efficient iteration
from itertools import islice, chain, groupby
first_100 = islice(huge_iterator, 100)  # No materialization
```

### Caching and Memoization

```python
from functools import lru_cache, cache

# Pattern: Cache expensive pure function results
@lru_cache(maxsize=1024)
def expensive_computation(key: str) -> Result:
    return compute(key)

# For unbounded cache (Python 3.9+)
@cache
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Manual caching with TTL for I/O results
_cache: dict[str, tuple[float, Result]] = {}

def cached_fetch(key: str, ttl: float = 300) -> Result:
    now = time.monotonic()
    if key in _cache:
        ts, result = _cache[key]
        if now - ts < ttl:
            return result
    result = fetch(key)
    _cache[key] = (now, result)
    return result
```

### Batching and Bulk Operations

```python
# Pattern: Batch I/O operations to reduce overhead

# Database: bulk insert instead of individual inserts
def insert_records(records: list[Record]) -> None:
    # Good: single query
    cursor.executemany(
        "INSERT INTO t (a, b) VALUES (?, ?)",
        [(r.a, r.b) for r in records]
    )
    # Bad: N queries
    # for r in records:
    #     cursor.execute("INSERT INTO t (a, b) VALUES (?, ?)", (r.a, r.b))

# HTTP: batch requests
async def fetch_all(urls: list[str]) -> list[Response]:
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[
            session.get(url) for url in urls
        ])
```

### String Building

```python
# Pattern: Efficient string concatenation

# Good: join for multiple strings
result = "".join(parts)
result = "\n".join(lines)

# Good: f-strings for formatting (fastest for simple cases)
msg = f"User {user_id} performed {action}"

# Good: io.StringIO for incremental building
from io import StringIO
buffer = StringIO()
for chunk in chunks:
    buffer.write(chunk)
result = buffer.getvalue()

# Bad: repeated concatenation (O(n²) in worst case)
# result = ""
# for part in parts:
#     result += part
```

### Precomputation and Lookup Tables

```python
# Pattern: Trade memory for speed with precomputed values

# Precompute regex patterns
import re
_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")  # Compile once

def extract_dates(text: str) -> list[str]:
    return _PATTERN.findall(text)

# Lookup tables for repeated calculations
_SIN_TABLE = [math.sin(math.radians(i)) for i in range(360)]

def fast_sin(degrees: int) -> float:
    return _SIN_TABLE[degrees % 360]
```

### Async I/O for Concurrent Operations

```python
import asyncio
from typing import TypeVar

T = TypeVar("T")

# Pattern: Use async for I/O-bound concurrency
async def fetch_with_semaphore(
    urls: list[str],
    max_concurrent: int = 10
) -> list[Response]:
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_fetch(url: str) -> Response:
        async with semaphore:
            return await fetch(url)
    
    return await asyncio.gather(*[bounded_fetch(u) for u in urls])
```

### __slots__ for Memory-Intensive Classes

```python
# Pattern: Use __slots__ for classes with many instances

class Point:
    __slots__ = ("x", "y", "z")
    
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

# Saves ~40-50% memory per instance vs regular class
# Also slightly faster attribute access
```

### Local Variable Optimization

```python
# Pattern: Localize frequently accessed globals/attributes in tight loops

def process_items(items: list[Item]) -> list[Result]:
    # Localize method lookup
    results_append = results.append
    process = expensive_module.process
    
    results: list[Result] = []
    for item in items:
        results_append(process(item))
    return results
```

## Anti-Patterns to Avoid

### Premature Optimization

```python
# Anti-pattern: Optimizing without profiling
# Wasted effort on non-bottlenecks

# Instead: Profile first
import cProfile
cProfile.run("main()", sort="cumulative")

# Or use line_profiler for line-by-line analysis
# @profile decorator + kernprof -l -v script.py
```

### N+1 Query Problem

```python
# Anti-pattern: Fetching related data in loops
for user in users:
    orders = db.query(Order).filter(Order.user_id == user.id).all()  # N queries!

# Fix: Eager loading / JOIN
users_with_orders = (
    db.query(User)
    .options(joinedload(User.orders))
    .all()
)  # 1 query
```

### Repeated Computation in Loops

```python
# Anti-pattern: Computing constants inside loops
for item in items:
    threshold = calculate_threshold(config)  # Same every iteration!
    if item.value > threshold:
        process(item)

# Fix: Hoist invariants
threshold = calculate_threshold(config)
for item in items:
    if item.value > threshold:
        process(item)
```

### Inefficient Data Structure Operations

```python
# Anti-pattern: O(n) operations in loops
for item in items:
    if item in large_list:  # O(n) per check = O(n²) total
        process(item)

# Fix: Convert to set for O(1) lookup
large_set = set(large_list)  # O(n) once
for item in items:
    if item in large_set:  # O(1) per check
        process(item)
```

### Blocking I/O in Async Code

```python
# Anti-pattern: Blocking calls in async functions
async def fetch_data():
    data = requests.get(url)  # Blocks entire event loop!
    return data

# Fix: Use async libraries
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Creating Objects in Hot Paths

```python
# Anti-pattern: Object creation in tight loops
for _ in range(1_000_000):
    result = SomeClass()  # Allocation overhead
    result.process(data)

# Fix: Reuse objects or use __slots__
processor = SomeClass()
for _ in range(1_000_000):
    processor.reset()
    processor.process(data)
```

### String Formatting in Logging

```python
# Anti-pattern: Eager string formatting
logger.debug(f"Processing {expensive_repr(obj)}")  # Always evaluated!

# Fix: Lazy formatting
logger.debug("Processing %s", obj)  # Only formatted if DEBUG enabled
```

### Catching Broad Exceptions for Flow Control

```python
# Anti-pattern: Using exceptions for expected cases
def get_value(d: dict, key: str) -> Any:
    try:
        return d[key]
    except KeyError:
        return None

# Fix: Use appropriate methods
def get_value(d: dict, key: str) -> Any:
    return d.get(key)  # No exception overhead
```

## Implementation Guidelines

### Step 1: Establish Baseline

```bash
# Profile CPU time
python -m cProfile -s cumulative script.py > profile.txt

# Profile memory
python -m memory_profiler script.py

# Benchmark specific functions
python -m timeit -s "from module import func" "func()"
```

### Step 2: Identify Bottlenecks

Focus on:
- Functions consuming >10% of total time
- Hot loops (high call count × time per call)
- Memory allocations in tight loops
- I/O operations (network, disk, database)

### Step 3: Apply Targeted Optimizations

Priority order:
1. **Algorithm/data structure changes** - Biggest impact
2. **I/O batching and caching** - Often 10-100x improvement
3. **Memory layout optimization** - Better cache utilization
4. **Micro-optimizations** - Only for proven hotspots

### Step 4: Validate Improvements

```python
# Use pytest-benchmark for regression testing
def test_performance(benchmark):
    result = benchmark(function_under_test, arg1, arg2)
    assert result == expected
```

### Step 5: Document Trade-offs

```python
# Document why optimization exists
# PERF: Using __slots__ saves ~45% memory for 1M+ instances
# Trade-off: Cannot add attributes dynamically
class OptimizedRecord:
    __slots__ = ("id", "value", "timestamp")
```

## Success Metrics

### Response Time
- P50, P95, P99 latency percentiles
- Target: P99 < 100ms for user-facing operations

### Throughput
- Requests/operations per second
- Target: Linear scaling with resources

### Memory Efficiency
- Peak memory usage
- Memory per operation/request
- Target: Stable memory under load (no leaks)

### CPU Utilization
- CPU time per operation
- Target: <10ms CPU time for typical operations

### I/O Efficiency
- Database queries per request
- Network round-trips per operation
- Target: Minimize to essential operations only

### Profiling Metrics
```python
# Track with decorators
import time
from functools import wraps

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("%s took %.3fs", func.__name__, elapsed)
        return result
    return wrapper
```

## Sources & References

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips) — Official Python wiki on performance
- [High Performance Python, 2nd Edition](https://www.oreilly.com/library/view/high-performance-python/9781492055013/) — Comprehensive optimization guide
- [Python Profilers Documentation](https://docs.python.org/3/library/profile.html) — Official profiling documentation
- [TimeComplexity - Python Wiki](https://wiki.python.org/moin/TimeComplexity) — Big-O for Python operations
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html) — Async I/O patterns
- [functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache) — Caching decorator documentation
- [Memory Management in Python](https://realpython.com/python-memory-management/) — Memory optimization techniques

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version with core patterns, anti-patterns, and implementation guidelines
