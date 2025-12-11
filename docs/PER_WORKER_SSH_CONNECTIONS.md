# Per-Worker SSH Connections

## Problem

Workers were experiencing severe SSH connection contention, causing:
- **10+ second delays** during concurrent command execution
- **Average command times 100x higher** than actual execution time
- Commands queuing and waiting for shared SSH connection

### Evidence
```
Command: dmesg
- Actual execution: 168ms
- Total duration: 10179ms
- Overhead: 10011ms (waiting for connection)

Command: ethtool
- Actual execution: 54ms
- Total duration: 10178ms  
- Overhead: 10124ms (waiting for connection)
```

## Solution

Implemented **per-worker SSH connections** to eliminate contention.

### Architecture Changes

**Before:**
```
Scanner → Single SSH Connection → All Workers (shared, serialized)
```

**After:**
```
Scanner → SSH Factory → Worker 1 (dedicated connection)
                      → Worker 2 (dedicated connection)
                      → Worker 3 (dedicated connection)
                      → ...
```

### Implementation

1. **Worker accepts SSH factory** instead of SSH instance
   - `Worker.__init__(ssh_factory)` creates connection on demand
   - Worker owns and manages its connection lifecycle
   - Connection created in `run()`, disconnected on exit

2. **Scanner provides SSH factory**
   - `BaseScanner._create_ssh_factory()` returns connection factory
   - `SutScanner._create_ssh_factory()` overrides with proper config
   - Factory creates connection with same credentials as scanner

3. **Connection lifecycle**
   - Worker creates connection when thread starts
   - Connection used exclusively by that worker
   - Worker disconnects when thread exits

### Code Changes

**src/core/worker.py:**
- Changed `__init__(ssh)` → `__init__(ssh_factory)`
- Added `_owns_connection` flag
- Create connection in `run()` before loop
- Disconnect in `run()` after loop

**src/models/scanner.py:**
- Changed `_add_worker_to_manager()` to pass factory
- Added `_create_ssh_factory()` base method

**src/core/scanner/sut.py:**
- Override `_create_ssh_factory()` with SUT-specific logic
- Factory creates LocalConnection or SSH connection based on config

## Benefits

### Performance
- **60-100x faster** command execution (no waiting)
- Commands execute in parallel without contention
- Actual execution time = measured time

### Reliability
- Worker failures isolated (don't affect other workers)
- Each worker can reconnect independently
- No single point of failure

### Scalability
- Can add more workers without performance degradation
- Linear scaling with worker count
- No bottleneck on shared resource

## Trade-offs

### Resource Usage
- **Memory**: ~50MB extra (6-8 connections × ~6-8MB each)
- **Network**: More TCP connections to remote host
- **Startup**: Slightly longer (parallel connection establishment)

### Complexity
- Workers manage own connection lifecycle
- Need factory pattern for connection creation
- More connections to monitor/debug

## Expected Results

### Before (Shared Connection)
```
dmesg:    Avg: 6382ms, Median: 9140ms
ethtool:  Avg: 6378ms, Median: 9121ms
ipmitool: Avg: 9347ms, Median: 9317ms
```

### After (Per-Worker Connections)
```
dmesg:    Avg: ~170ms, Median: ~170ms (60x faster)
ethtool:  Avg: ~55ms,  Median: ~55ms  (100x faster)
ipmitool: Avg: ~8800ms, Median: ~8800ms (no change, command is slow)
```

## Configuration

No configuration changes needed. The system automatically:
- Creates one connection per worker
- Uses same credentials as scanner
- Manages connection lifecycle

## Monitoring

Check logs for:
```
DEBUG - Worker Thread-X established SSH connection
DEBUG - Worker Thread-X disconnected SSH connection
```

## Rollback

To revert to shared connection (not recommended):
1. Change `Worker.__init__(ssh_factory)` → `Worker.__init__(ssh)`
2. Change `_add_worker_to_manager()` to pass `self._ssh`
3. Remove connection creation/cleanup in `Worker.run()`

## Future Improvements

1. **Connection pooling**: Reuse connections across workers
2. **Lazy connection**: Only connect when first command executes
3. **Connection health checks**: Periodic keepalive/reconnection
4. **Configurable strategy**: Allow shared vs per-worker via config
