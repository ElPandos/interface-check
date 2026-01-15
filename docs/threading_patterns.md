---
title:        Python Threading Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Python Threading Patterns

## Core Principles

1. **GIL Awareness**: Python's Global Interpreter Lock prevents true CPU parallelism—use threading for I/O-bound tasks only, multiprocessing for CPU-bound work
2. **Atomicity Assumption is Wrong**: Compound operations like `i += 1` are NOT atomic; context switches occur at bytecode level, not Python code level
3. **Context Managers Always**: Use `with lock:` syntax—never bare `acquire()`/`release()` calls
4. **Explicit Synchronization**: Use `join()`, `Event`, `Barrier`, `Condition`—never `time.sleep()` for coordination
5. **Lock Ordering**: Acquire multiple locks in consistent global order to prevent deadlocks

## Essential Patterns

### ThreadPoolExecutor (Preferred for Most Cases)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_items(items: list[str]) -> list[Result]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process, item): item for item in items}
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result(timeout=30))
            except Exception as e:
                logger.exception("Task failed: %s", futures[future])
        return results
```

**Why**: Manages thread lifecycle, handles exceptions cleanly, supports graceful shutdown.

### Producer-Consumer with Queue

```python
from queue import Queue
from threading import Thread, Event

def producer(q: Queue, stop: Event) -> None:
    while not stop.is_set():
        item = generate_item()
        q.put(item)  # Thread-safe, blocks if full

def consumer(q: Queue, stop: Event) -> None:
    while not stop.is_set() or not q.empty():
        try:
            item = q.get(timeout=1)
            process(item)
            q.task_done()
        except Empty:
            continue
```

**Why**: `queue.Queue` is thread-safe; decouples production from consumption.

### Event-Based Coordination

```python
from threading import Event, Thread

ready = Event()

def worker(ready: Event) -> None:
    # Setup work...
    ready.set()  # Signal ready
    # Continue work...

def main() -> None:
    t = Thread(target=worker, args=(ready,))
    t.start()
    ready.wait(timeout=10)  # Block until ready or timeout
    # Proceed knowing worker is ready
```

**Why**: Clean signaling without polling or sleep loops.

### Barrier for Phased Execution

```python
from threading import Barrier, Thread

barrier = Barrier(3)  # Wait for 3 threads

def phase_worker(barrier: Barrier) -> None:
    do_phase_1()
    barrier.wait()  # All threads sync here
    do_phase_2()
    barrier.wait()  # Sync again
    do_phase_3()
```

**Why**: Ensures all threads complete each phase before any proceeds.

### RLock for Recursive Acquisition

```python
from threading import RLock

class Counter:
    def __init__(self) -> None:
        self._lock = RLock()
        self._value = 0

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    def add_multiple(self, n: int) -> None:
        with self._lock:  # Can acquire same lock
            for _ in range(n):
                self.increment()  # Nested acquisition OK
```

**Why**: Allows same thread to acquire lock multiple times without deadlock.

## Anti-Patterns to Avoid

### 1. Relying on GIL for Thread Safety

```python
# WRONG - Race condition despite GIL
counter = 0
def increment():
    global counter
    counter += 1  # NOT atomic: LOAD, ADD, STORE are separate bytecodes

# CORRECT
from threading import Lock
lock = Lock()
counter = 0
def increment():
    global counter
    with lock:
        counter += 1
```

### 2. Bare Lock Acquisition

```python
# WRONG - Exception leaves lock held forever
lock.acquire()
do_work()  # If this raises, lock never released
lock.release()

# CORRECT
with lock:
    do_work()  # Lock released even on exception
```

### 3. Sleep-Based Coordination

```python
# WRONG - Wastes time, unreliable
def wait_for_ready():
    while not ready:
        time.sleep(0.1)  # Polling is wasteful

# CORRECT
ready_event = Event()
ready_event.wait(timeout=10)  # Efficient blocking
```

### 4. Inconsistent Lock Ordering

```python
# WRONG - Deadlock risk
def transfer_a_to_b():
    with lock_a:
        with lock_b:
            ...

def transfer_b_to_a():
    with lock_b:  # Different order!
        with lock_a:
            ...

# CORRECT - Always same order
def transfer(from_lock, to_lock):
    locks = sorted([from_lock, to_lock], key=id)
    with locks[0]:
        with locks[1]:
            ...
```

### 5. Not Using Timeouts

```python
# WRONG - Hangs forever on deadlock
lock.acquire()

# CORRECT - Detect deadlock
if not lock.acquire(timeout=5):
    raise TimeoutError("Possible deadlock")
```

## Implementation Guidelines

### ThreadPoolExecutor Shutdown

```python
# Python 3.9+
executor.shutdown(wait=True, cancel_futures=True)

# Python 3.8 and below - manual cancellation
executor.shutdown(wait=False)
for future in futures:
    future.cancel()
```

### Daemon Threads for Background Work

```python
# Daemon threads auto-terminate when main thread exits
thread = Thread(target=background_task, daemon=True)
thread.start()
# No need to join - dies with main thread
```

### Graceful Shutdown Pattern

```python
from threading import Thread, Event

class Worker:
    def __init__(self) -> None:
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._do_work()
```

### Thread-Local Storage

```python
import threading

local = threading.local()

def get_connection():
    if not hasattr(local, 'conn'):
        local.conn = create_connection()
    return local.conn
```

## Synchronization Primitive Selection

| Primitive | Use Case |
|-----------|----------|
| `Lock` | Mutual exclusion for shared resource |
| `RLock` | Same thread needs nested acquisition |
| `Semaphore` | Limit concurrent access (e.g., connection pool) |
| `BoundedSemaphore` | Semaphore with release count validation |
| `Event` | One-time or toggle signaling between threads |
| `Condition` | Complex wait/notify patterns |
| `Barrier` | Synchronize N threads at checkpoints |
| `Queue` | Thread-safe producer-consumer |

## Success Metrics

- Zero deadlocks in production
- No race conditions detected via stress testing
- Clean shutdown within timeout bounds
- Thread count stays bounded (no leaks)
- CPU usage appropriate for I/O-bound workload (low)

## Sources & References

- [Thread Deadlock in Python](https://superfastpython.com/thread-deadlock-in-python/) — Deadlock identification and prevention patterns
- [ThreadPoolExecutor Shutdown](https://superfastpython.com/threadpoolexecutor-shutdown/) — Proper executor lifecycle management
- [Python Threading Lock](https://realpython.com/python-thread-lock/) — Locks, semaphores, events, conditions, barriers
- [5 Threading Anti-Patterns](https://superfastpython.com/) — GIL misconceptions, atomicity, context managers

## Version History

- v1.0 (2025-01-13 00:00:00): Initial version from research on threading patterns and anti-patterns
