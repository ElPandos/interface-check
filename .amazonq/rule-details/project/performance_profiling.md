# Performance Profiling and Optimization

## Profiling Tools and Techniques

### Python Profiling
```python
import cProfile
import pstats
from functools import wraps
import time

def profile_function(func):
    """Decorator to profile function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

@profile_function
def expensive_operation():
    # Your code here
    pass
```

### Timing Decorators
```python
import time
import logging
from functools import wraps

def time_operation(operation_name: str):
    """Decorator to time operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                logging.info(f"{operation_name} took {duration:.3f} seconds")
        return wrapper
    return decorator

@time_operation("SSH Command Execution")
def execute_ssh_command(command: str):
    # SSH execution code
    pass
```

## Memory Optimization

### Memory Profiling
```python
from pympler import tracker, muppy, summary
import gc

class MemoryTracker:
    """Track memory usage patterns."""
    
    def __init__(self):
        self.tracker = tracker.SummaryTracker()
        
    def start_tracking(self):
        """Start memory tracking."""
        self.tracker.print_diff()
        
    def print_memory_diff(self):
        """Print memory usage differences."""
        self.tracker.print_diff()
        
    def get_memory_summary(self):
        """Get current memory summary."""
        all_objects = muppy.get_objects()
        return summary.summarize(all_objects)

# Usage
memory_tracker = MemoryTracker()
memory_tracker.start_tracking()
# ... perform operations ...
memory_tracker.print_memory_diff()
```

### Data Structure Optimization
```python
from collections import deque
from typing import Dict, List
import sys

# Use deque for FIFO operations
class CircularBuffer:
    """Memory-efficient circular buffer."""
    
    def __init__(self, maxsize: int):
        self.buffer = deque(maxlen=maxsize)
        
    def append(self, item):
        self.buffer.append(item)
        
    def get_recent(self, n: int) -> List:
        return list(self.buffer)[-n:]

# Use __slots__ for memory efficiency
class NetworkMetric:
    __slots__ = ['timestamp', 'interface', 'rx_bytes', 'tx_bytes']
    
    def __init__(self, timestamp: float, interface: str, rx_bytes: int, tx_bytes: int):
        self.timestamp = timestamp
        self.interface = interface
        self.rx_bytes = rx_bytes
        self.tx_bytes = tx_bytes
```

## SSH Performance Optimization

### Connection Pooling
```python
import threading
from queue import Queue, Empty
from contextlib import contextmanager

class SSHConnectionPool:
    """Pool of SSH connections for reuse."""
    
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.pool: Queue[SshConnection] = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()
        
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        connection = None
        try:
            # Try to get existing connection
            connection = self.pool.get_nowait()
        except Empty:
            # Create new connection if pool is empty
            with self.lock:
                if self.active_connections < self.max_connections:
                    connection = SshConnection()
                    connection.connect()
                    self.active_connections += 1
                    
        if connection is None:
            # Wait for available connection
            connection = self.pool.get()
            
        try:
            yield connection
        finally:
            # Return connection to pool
            if connection.is_connected():
                self.pool.put(connection)
            else:
                with self.lock:
                    self.active_connections -= 1
```

### Command Batching
```python
def batch_ssh_commands(commands: List[str], ssh_connection: SshConnection) -> Dict[str, tuple[str, str]]:
    """Execute multiple commands in a single SSH session."""
    # Combine commands with separators
    combined_command = " && ".join([
        f"echo 'START_{i}' && {cmd} && echo 'END_{i}'"
        for i, cmd in enumerate(commands)
    ])
    
    stdout, stderr = ssh_connection.exec_command(combined_command)
    
    # Parse combined output
    results = {}
    current_output = []
    current_cmd_idx = None
    
    for line in stdout.split('\n'):
        if line.startswith('START_'):
            current_cmd_idx = int(line.split('_')[1])
            current_output = []
        elif line.startswith('END_'):
            if current_cmd_idx is not None:
                results[commands[current_cmd_idx]] = ('\n'.join(current_output), '')
        else:
            current_output.append(line)
            
    return results
```

## UI Performance Optimization

### Debouncing and Throttling
```python
import asyncio
from functools import wraps

def debounce(wait_time: float):
    """Debounce function calls."""
    def decorator(func):
        last_call_time = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_call_time
            current_time = time.time()
            
            if current_time - last_call_time >= wait_time:
                last_call_time = current_time
                return await func(*args, **kwargs)
                
        return wrapper
    return decorator

@debounce(0.5)  # 500ms debounce
async def search_interfaces(query: str):
    # Search implementation
    pass
```

### Virtual Scrolling for Large Data
```python
class VirtualScrollList:
    """Virtual scrolling implementation for large datasets."""
    
    def __init__(self, items: List, item_height: int = 50, visible_count: int = 10):
        self.items = items
        self.item_height = item_height
        self.visible_count = visible_count
        self.scroll_top = 0
        
    def get_visible_items(self) -> tuple[int, int, List]:
        """Get currently visible items."""
        start_index = max(0, self.scroll_top // self.item_height)
        end_index = min(len(self.items), start_index + self.visible_count)
        
        visible_items = self.items[start_index:end_index]
        return start_index, end_index, visible_items
        
    def update_scroll(self, scroll_position: int):
        """Update scroll position."""
        self.scroll_top = scroll_position
```

## Benchmarking

### Performance Benchmarks
```python
import timeit
from typing import Callable

def benchmark_function(func: Callable, *args, number: int = 1000, **kwargs) -> float:
    """Benchmark function execution time."""
    def wrapper():
        return func(*args, **kwargs)
        
    execution_time = timeit.timeit(wrapper, number=number)
    avg_time = execution_time / number
    
    print(f"Function {func.__name__}:")
    print(f"  Total time: {execution_time:.4f}s")
    print(f"  Average time: {avg_time:.6f}s")
    print(f"  Executions per second: {1/avg_time:.0f}")
    
    return avg_time

# Usage
benchmark_function(parse_ethtool_output, sample_output)
```