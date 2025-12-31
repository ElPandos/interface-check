---
title: Threading Patterns
inclusion: always
---

# Threading Patterns

## Worker Thread Management
- **Daemon Threads**: Background tasks use daemon threads with proper lifecycle management
- **Stop Events**: Graceful shutdown using threading.Event() for clean termination
- **Thread Safety**: Queue-based communication between threads
- **Exception Isolation**: Thread exceptions don't crash main application

## Data Collection Threading
- **Periodic Collection**: Regular interval data gathering with configurable timing
- **Queue Management**: Limited queue sizes to prevent memory issues
- **Latest Data Pattern**: Keep only most recent data, discard old entries
- **Timeout Handling**: Non-blocking operations with appropriate timeouts

## Thread-Safe UI Updates
- **NiceGUI Integration**: Safe UI updates from background threads
- **Async Coordination**: Use asyncio.create_task for thread-to-UI communication
- **Event-Driven Updates**: UI responds to data changes via events
- **Resource Cleanup**: Proper cleanup of UI resources on thread termination

## Communication Patterns
- **Queue-Based**: Use queue.Queue for thread-safe data exchange
- **Event Coordination**: threading.Event for thread synchronization
- **Bounded Queues**: Limit queue sizes to prevent memory growth
- **Non-Blocking Operations**: Prefer get_nowait() and put_nowait() patterns

## Resource Management
- **Context Managers**: Automatic thread lifecycle management
- **Timeout Patterns**: All join() operations include timeout parameters
- **Graceful Shutdown**: Stop events with reasonable timeout periods
- **Memory Management**: Clear queues and release resources on shutdown

## Best Practices
- Always implement stop mechanisms with timeouts
- Use daemon threads for background operations
- Handle exceptions within threads to prevent crashes
- Avoid shared mutable state without proper locking
- Use events for coordination between threads
- Implement proper cleanup in finally blocks
