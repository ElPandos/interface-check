---
title:        Threading Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Threading Best Practices

## Core Principles

1. **Use Threading for I/O-Bound Tasks Only**: Due to Python's Global Interpreter Lock (GIL), threads cannot execute Python bytecode in parallel. Threading excels at I/O-bound operations (network requests, file operations, database queries) where threads spend time waiting for external resources.

2. **Prefer High-Level Abstractions**: Use `concurrent.futures.ThreadPoolExecutor` over raw `threading.Thread`. It provides cleaner lifecycle management, automatic thread pooling, and Future-based result handling.

3. **Protect Shared State with Synchronization Primitives**: Race conditions occur even with the GIL. Always use locks, semaphores, or thread-safe data structures when multiple threads access shared mutable state.

4. **Design for Thread Safety from the Start**: Retrofitting thread safety is error-prone. Prefer immutable data, thread-local storage, and message-passing patterns over shared mutable state.

5. **Embrace Python 3.13+ Free-Threading (Experimental)**: Python 3.13 introduced experimental GIL-free builds enabling true parallelism. Monitor this feature for CPU-bound workloads as it matures in Python 3.14+.

## Essential Practices

### ThreadPoolExecutor Usage

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar

T = TypeVar("T")

def parallel_io_tasks(
    func: Callable[..., T],
    items: list,
    max_workers: int | None = None,
) -> list[T]:
    """Execute I/O-bound tasks in parallel with proper resource management."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): item for item in items}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                # Log and handle per-task failures
                logger.exception("Task failed for %s: %s", futures[future], e)
    return results
```

### Lock Usage with Context Managers

```python
import threading
from contextlib import contextmanager
from typing import Generator

class ThreadSafeCounter:
    """Thread-safe counter using lock context manager."""
    
    __slots__ = ("_value", "_lock")
    
    def __init__(self, initial: int = 0) -> None:
        self._value = initial
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1) -> int:
        with self._lock:  # Always use context manager
            self._value += amount
            return self._value
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value
```

### Producer-Consumer with queue.Queue

```python
import queue
import threading
from typing import Any, Callable

def producer_consumer(
    producer_fn: Callable[[], Any],
    consumer_fn: Callable[[Any], None],
    num_producers: int = 1,
    num_consumers: int = 2,
    sentinel: object = None,
) -> None:
    """Thread-safe producer-consumer pattern using queue.Queue."""
    q: queue.Queue[Any] = queue.Queue(maxsize=100)
    
    def producer() -> None:
        for item in producer_fn():
            q.put(item)
        q.put(sentinel)  # Signal completion
    
    def consumer() -> None:
        while True:
            item = q.get()
            if item is sentinel:
                q.put(sentinel)  # Propagate sentinel
                break
            try:
                consumer_fn(item)
            finally:
                q.task_done()
    
    producers = [threading.Thread(target=producer, daemon=True) for _ in range(num_producers)]
    consumers = [threading.Thread(target=consumer, daemon=True) for _ in range(num_consumers)]
    
    for t in producers + consumers:
        t.start()
    for t in producers:
        t.join()
    q.join()
```

### Thread Coordination with Events

```python
import threading

class GracefulWorker:
    """Worker thread with proper shutdown coordination."""
    
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
    
    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
    
    def _run(self) -> None:
        while not self._stop_event.is_set():
            # Do work, check stop_event periodically
            if self._stop_event.wait(timeout=0.1):
                break
```

### Thread-Local Storage

```python
import threading
from typing import TypeVar

T = TypeVar("T")

class ThreadLocalCache:
    """Per-thread cache avoiding shared state."""
    
    def __init__(self) -> None:
        self._local = threading.local()
    
    def get(self, key: str, factory: Callable[[], T]) -> T:
        cache = getattr(self._local, "cache", None)
        if cache is None:
            cache = {}
            self._local.cache = cache
        if key not in cache:
            cache[key] = factory()
        return cache[key]
```

## Anti-Patterns to Avoid

### 1. Relying on the GIL for Thread Safety

```python
# WRONG: Assumes GIL prevents race conditions
counter = 0
def increment():
    global counter
    counter += 1  # NOT atomic - read/modify/write

# CORRECT: Use explicit synchronization
lock = threading.Lock()
def increment_safe():
    global counter
    with lock:
        counter += 1
```

### 2. Assuming Operations Are Atomic

```python
# WRONG: List operations seem atomic but aren't always
shared_list = []
def append_item(item):
    if item not in shared_list:  # Check
        shared_list.append(item)  # Then act - RACE CONDITION

# CORRECT: Use thread-safe queue or lock
from queue import Queue
safe_queue: Queue = Queue()
```

### 3. Not Using Context Managers for Locks

```python
# WRONG: Lock may never be released on exception
lock.acquire()
do_risky_operation()  # If this raises, lock is held forever
lock.release()

# CORRECT: Context manager ensures release
with lock:
    do_risky_operation()
```

### 4. Coordinating Threads with sleep()

```python
# WRONG: Fragile timing-based coordination
def wait_for_result():
    time.sleep(5)  # Hope the other thread finished
    return shared_result

# CORRECT: Use proper synchronization
result_ready = threading.Event()
def wait_for_result():
    result_ready.wait()  # Block until signaled
    return shared_result
```

### 5. Inconsistent Lock Usage

```python
# WRONG: Only some accesses protected
with lock:
    data["key"] = value

# Elsewhere, unprotected read - RACE CONDITION
print(data["key"])

# CORRECT: ALL accesses must be protected
with lock:
    print(data["key"])
```

### 6. Creating Threads in Loops Without Pooling

```python
# WRONG: Thread creation overhead, no limit
for url in urls:
    threading.Thread(target=fetch, args=(url,)).start()

# CORRECT: Use thread pool
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(fetch, urls)
```

### 7. Deadlock from Lock Ordering

```python
# WRONG: Inconsistent lock ordering causes deadlock
# Thread 1: lock_a -> lock_b
# Thread 2: lock_b -> lock_a

# CORRECT: Always acquire locks in consistent order
locks = sorted([lock_a, lock_b], key=id)
for lock in locks:
    lock.acquire()
```

## Implementation Guidelines

### Step 1: Identify Concurrency Requirements

- Determine if tasks are I/O-bound (use threading) or CPU-bound (use multiprocessing)
- Identify shared state that requires protection
- Define thread lifecycle and shutdown requirements

### Step 2: Choose the Right Abstraction

| Use Case | Recommended Approach |
|----------|---------------------|
| Parallel I/O tasks | `ThreadPoolExecutor` |
| Background worker | `threading.Thread` with `Event` |
| Task queue | `queue.Queue` + worker threads |
| Periodic tasks | `threading.Timer` or scheduler |
| High-concurrency I/O | `asyncio` (single-threaded) |

### Step 3: Implement Thread Safety

1. Minimize shared mutable state
2. Use `queue.Queue` for thread communication
3. Protect remaining shared state with `threading.Lock`
4. Use `threading.RLock` only when reentrant locking is required
5. Prefer `threading.Event` and `threading.Condition` over polling

### Step 4: Handle Errors and Shutdown

```python
class ManagedThreadPool:
    """Thread pool with graceful shutdown."""
    
    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: list[Future] = []
    
    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        future = self._executor.submit(fn, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def shutdown(self, wait: bool = True, timeout: float | None = None) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=not wait)
        if wait and timeout:
            for future in self._futures:
                try:
                    future.result(timeout=timeout)
                except Exception:
                    pass
```

### Step 5: Test Concurrent Code

- Use `threading.Barrier` to synchronize test threads
- Run tests with thread sanitizers when available
- Test with varying thread counts and timing
- Use `unittest.mock` to inject delays and failures

## Success Metrics

### Correctness Metrics

- **Zero race conditions**: No data corruption under concurrent access
- **No deadlocks**: All threads complete or timeout gracefully
- **Consistent state**: Shared data remains valid after concurrent operations

### Performance Metrics

- **Thread utilization**: Threads spend minimal time blocked
- **Throughput**: Tasks completed per second meets requirements
- **Latency**: P99 response time within acceptable bounds
- **Resource efficiency**: Thread count scales appropriately with workload

### Operational Metrics

- **Graceful shutdown**: All threads terminate within timeout
- **Error isolation**: Single task failure doesn't crash pool
- **Observability**: Thread states and queue depths are logged/monitored

### Code Quality Metrics

- **Lock coverage**: All shared state accesses are protected
- **Context manager usage**: 100% of lock acquisitions use `with` statement
- **Type safety**: All threading code passes `mypy --strict`

## Sources & References

- [Real Python - Thread Lock and Safety](https://realpython.com/python-thread-lock/) — Comprehensive guide on locks, semaphores, events, conditions, and barriers. Accessed 2026-01-14

- [SuperFastPython - 5 Threading Anti-Patterns](https://superfastpython.com/thread-anti-patterns/) — Detailed analysis of common threading mistakes and solutions. Accessed 2026-01-14

- [Python Documentation - threading module](https://docs.python.org/3/library/threading.html) — Official threading module reference

- [Python Documentation - concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) — Official ThreadPoolExecutor documentation

- [Python Documentation - queue module](https://docs.python.org/3/library/queue.html) — Thread-safe queue implementations

- [PEP 703 - Making the GIL Optional](https://peps.python.org/pep-0703/) — Free-threaded Python specification for Python 3.13+

- [GeeksforGeeks - Asyncio vs Threading](https://www.geeksforgeeks.org/asyncio-vs-threading-in-python/) — Comparison of concurrency approaches. Accessed 2026-01-14

- [DZone - Breaking the GIL in Python 3.14](https://dzone.com/articles/breaking-the-chains-of-the-gil-in-python) — Free-threading maturity in Python 3.14. Accessed 2026-01-14

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
