---
title:        Threading Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Threading Best Practices

## Purpose
Establish comprehensive threading practices for safe, efficient, and maintainable concurrent programming while avoiding common pitfalls like deadlocks and race conditions.

## Core Principles

### 1. Deadlock Prevention
- **Consistent Lock Ordering**: Always acquire locks in the same order across all threads
- **Avoid Multiple Locks**: Minimize holding multiple locks simultaneously
- **Timeout Mechanisms**: Use try-lock with timeouts to prevent indefinite waiting
- **Lock Hierarchy**: Establish a global lock acquisition order
- **Short Critical Sections**: Keep lock duration minimal to reduce contention

### 2. Race Condition Prevention
- **Atomic Operations**: Use atomic operations for simple shared data modifications
- **Synchronization Primitives**: Proper use of mutexes, semaphores, and condition variables
- **Thread-Safe Data Structures**: Use concurrent collections and thread-safe libraries
- **Immutable Data**: Prefer immutable objects to eliminate shared mutable state
- **Local Variables**: Use local variables over instance variables for temporary data

### 3. Thread Safety Design
- **Immutable Objects**: Design objects that cannot be modified after creation
- **Thread Confinement**: Restrict object access to single threads
- **Stateless Design**: Create stateless components that don't share mutable state
- **Message Passing**: Use message queues instead of shared memory
- **Actor Model**: Implement actor-based concurrency patterns

## Synchronization Strategies

### 1. Locking Mechanisms
- **Fine-Grained Locking**: Use specific locks for different data sections
- **Read-Write Locks**: Allow multiple readers or single writer access patterns
- **Scoped Locking**: Use RAII-style lock guards for automatic lock release
- **Lock-Free Programming**: Use atomic operations and compare-and-swap techniques
- **Hierarchical Locking**: Establish lock ordering to prevent circular dependencies

### 2. High-Level Synchronization
- **Thread Pools**: Manage thread lifecycle efficiently with pools
- **Barriers**: Synchronize multiple threads at specific execution points
- **Semaphores**: Control access to limited resources
- **Condition Variables**: Wait for specific conditions before proceeding
- **Futures/Promises**: Handle asynchronous computation results

### 3. Lock-Free Techniques
- **Atomic Operations**: Use hardware-supported atomic operations
- **Compare-and-Swap**: Implement lock-free data structures
- **Memory Ordering**: Understand and use appropriate memory ordering constraints
- **Hazard Pointers**: Manage memory in lock-free data structures
- **RCU (Read-Copy-Update)**: Efficient read-mostly data structure updates

## Resource Management

### 1. RAII Pattern
- **Automatic Cleanup**: Use Resource Acquisition Is Initialization for automatic cleanup
- **Exception Safety**: Ensure resources are released even when exceptions occur
- **Scoped Resources**: Tie resource lifetime to scope
- **Smart Pointers**: Use smart pointers for automatic memory management
- **Custom Destructors**: Implement proper cleanup in destructors

### 2. Thread Lifecycle Management
- **Thread Creation**: Use thread pools instead of creating threads frequently
- **Graceful Shutdown**: Implement proper thread termination mechanisms
- **Join Operations**: Always join or detach threads to avoid resource leaks
- **Thread Affinity**: Bind threads to specific CPU cores when beneficial
- **Work Stealing**: Implement work-stealing algorithms for load balancing

## Common Threading Patterns

### 1. Producer-Consumer Pattern
```cpp
class ProducerConsumer {
private:
    std::queue<Item> buffer;
    std::mutex mtx;
    std::condition_variable cv;
    bool finished = false;

public:
    void produce(Item item) {
        std::lock_guard<std::mutex> lock(mtx);
        buffer.push(item);
        cv.notify_one();
    }
    
    bool consume(Item& item) {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this] { return !buffer.empty() || finished; });
        
        if (buffer.empty()) return false;
        
        item = buffer.front();
        buffer.pop();
        return true;
    }
};
```

### 2. Reader-Writer Pattern
```cpp
class ReaderWriter {
private:
    std::shared_mutex rw_mutex;
    Data shared_data;

public:
    Data read() {
        std::shared_lock<std::shared_mutex> lock(rw_mutex);
        return shared_data;
    }
    
    void write(const Data& data) {
        std::unique_lock<std::shared_mutex> lock(rw_mutex);
        shared_data = data;
    }
};
```

### 3. Thread-Safe Singleton
```cpp
class Singleton {
private:
    static std::once_flag initialized;
    static std::unique_ptr<Singleton> instance;
    
    Singleton() = default;

public:
    static Singleton& getInstance() {
        std::call_once(initialized, []() {
            instance = std::make_unique<Singleton>();
        });
        return *instance;
    }
};
```

## Deadlock Prevention Techniques

### 1. Coffman Conditions
Break one or more of the four necessary conditions for deadlock:
- **Mutual Exclusion**: Use lock-free algorithms when possible
- **Hold and Wait**: Acquire all locks at once or use timeouts
- **No Preemption**: Allow lock preemption with timeouts
- **Circular Wait**: Establish lock ordering to prevent cycles

### 2. Lock Ordering Strategy
```cpp
class BankAccount {
private:
    std::mutex mtx;
    int balance;
    int account_id;

public:
    static void transfer(BankAccount& from, BankAccount& to, int amount) {
        // Always lock accounts in order of account_id to prevent deadlock
        BankAccount& first = (from.account_id < to.account_id) ? from : to;
        BankAccount& second = (from.account_id < to.account_id) ? to : from;
        
        std::lock_guard<std::mutex> lock1(first.mtx);
        std::lock_guard<std::mutex> lock2(second.mtx);
        
        from.balance -= amount;
        to.balance += amount;
    }
};
```

### 3. Timeout-Based Locking
```cpp
bool tryTransfer(BankAccount& from, BankAccount& to, int amount) {
    std::unique_lock<std::mutex> lock1(from.mtx, std::defer_lock);
    std::unique_lock<std::mutex> lock2(to.mtx, std::defer_lock);
    
    if (std::try_lock(lock1, lock2) == -1) {
        from.balance -= amount;
        to.balance += amount;
        return true;
    }
    return false; // Could not acquire both locks
}
```

## Performance Optimization

### 1. Lock Contention Reduction
- **Minimize Lock Duration**: Keep critical sections as short as possible
- **Reduce Lock Scope**: Use fine-grained locking instead of coarse-grained
- **Lock Splitting**: Split single locks into multiple locks for different data
- **Lock Striping**: Use multiple locks for different hash buckets
- **Read-Write Separation**: Use read-write locks for read-heavy workloads

### 2. Cache-Friendly Programming
- **False Sharing Avoidance**: Pad data structures to avoid cache line conflicts
- **Data Locality**: Keep related data close together in memory
- **Cache Line Alignment**: Align frequently accessed data to cache boundaries
- **Memory Access Patterns**: Design algorithms with good spatial locality
- **Thread-Local Storage**: Use thread-local variables to avoid sharing

## Testing and Debugging

### 1. Concurrency Testing
- **Stress Testing**: Test under high concurrency and load conditions
- **Race Detection**: Use ThreadSanitizer, Helgrind, or similar tools
- **Deadlock Detection**: Implement or use tools for deadlock detection
- **Deterministic Testing**: Create reproducible test scenarios
- **Property-Based Testing**: Test concurrent properties with random inputs

### 2. Debugging Tools
- **Static Analysis**: Use tools to detect potential concurrency issues
- **Dynamic Analysis**: Runtime detection of race conditions and deadlocks
- **Profiling**: Identify performance bottlenecks in concurrent code
- **Logging**: Implement thread-safe logging for debugging
- **Visualization**: Use tools to visualize thread interactions

## Language-Specific Guidelines

### 1. C++ Threading
- Use `std::thread`, `std::mutex`, and `std::atomic`
- Prefer RAII patterns with lock guards
- Use `std::shared_ptr` for shared ownership
- Leverage `std::async` for simple parallel tasks

### 2. Java Threading
- Use `java.util.concurrent` package
- Prefer `ExecutorService` over raw threads
- Use `ConcurrentHashMap` instead of synchronized collections
- Implement proper exception handling in threads

### 3. Python Threading
- Understand GIL limitations for CPU-bound tasks
- Use `multiprocessing` for CPU-intensive work
- Use `threading` for I/O-bound tasks
- Prefer `queue.Queue` for thread communication

## Common Anti-Patterns to Avoid

### 1. Threading Mistakes
- **Double-Checked Locking**: Often implemented incorrectly
- **Busy Waiting**: Avoid spinning loops, use proper synchronization
- **Excessive Locking**: Over-synchronization hurts performance
- **Shared Mutable State**: Minimize shared mutable data between threads
- **Thread Creation Overhead**: Don't create threads for short-lived tasks

### 2. Synchronization Issues
- **Nested Locking**: Avoid holding multiple locks when possible
- **Long Critical Sections**: Keep synchronized blocks short
- **Inconsistent Locking**: Always use the same locking strategy
- **Missing Synchronization**: Ensure all shared data access is synchronized
- **Deadlock-Prone Patterns**: Avoid circular lock dependencies

## Best Practices Summary

### 1. Design Principles
- Design for thread safety from the beginning
- Minimize shared mutable state
- Use high-level concurrency abstractions when possible
- Prefer immutable objects and functional programming patterns
- Document thread safety guarantees and requirements

### 2. Implementation Guidelines
- Use established patterns and avoid reinventing synchronization
- Test thoroughly with stress testing and race detection tools
- Profile and optimize based on actual performance data
- Implement proper error handling and resource cleanup
- Monitor and measure concurrent system performance

### 3. Maintenance Practices
- Regular code reviews focusing on concurrency issues
- Continuous integration with concurrency testing
- Performance monitoring in production
- Documentation of threading assumptions and guarantees
- Team training on concurrent programming best practices

## Version History

- v1.0 (2026-01-12): Initial version based on industry research and concurrent programming best practices
