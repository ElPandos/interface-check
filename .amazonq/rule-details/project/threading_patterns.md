# Threading and Concurrency Patterns

## Background Task Management

### Worker Thread Pattern
```python
import threading
import queue
from typing import Callable, Any

class BackgroundWorker:
    """Manages background tasks with proper lifecycle."""
    
    def __init__(self, name: str):
        self.name = name
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._task_queue: queue.Queue[Callable] = queue.Queue()
        
    def start(self) -> None:
        """Start the worker thread."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the worker thread gracefully."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            
    def submit_task(self, task: Callable[[], Any]) -> None:
        """Submit a task to be executed in background."""
        self._task_queue.put(task)
        
    def _worker_loop(self) -> None:
        """Main worker loop."""
        while not self._stop_event.is_set():
            try:
                task = self._task_queue.get(timeout=1.0)
                task()
                self._task_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                logger.exception(f"Task failed in {self.name}")
```

## Data Collection Threading

### Periodic Data Collection
```python
class PeriodicCollector:
    """Collects data at regular intervals."""
    
    def __init__(self, interval: float, collector_func: Callable[[], Any]):
        self.interval = interval
        self.collector_func = collector_func
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._data_queue: queue.Queue[Any] = queue.Queue(maxsize=1000)
        
    def start_collection(self) -> None:
        """Start periodic data collection."""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._thread.start()
        
    def stop_collection(self) -> None:
        """Stop data collection."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            
    def get_latest_data(self) -> Any | None:
        """Get the most recent data point."""
        try:
            return self._data_queue.get_nowait()
        except queue.Empty:
            return None
            
    def _collection_loop(self) -> None:
        """Main collection loop."""
        while not self._stop_event.is_set():
            try:
                data = self.collector_func()
                if data is not None:
                    # Keep only latest data, discard old
                    try:
                        self._data_queue.put_nowait(data)
                    except queue.Full:
                        # Remove old data and add new
                        try:
                            self._data_queue.get_nowait()
                            self._data_queue.put_nowait(data)
                        except queue.Empty:
                            pass
            except Exception:
                logger.exception("Data collection failed")
                
            self._stop_event.wait(self.interval)
```

## Thread-Safe UI Updates

### NiceGUI Thread Safety
```python
from nicegui import ui
import asyncio

class ThreadSafeUIUpdater:
    """Safely update UI from background threads."""
    
    @staticmethod
    def update_label(label: ui.label, text: str) -> None:
        """Update label text from any thread."""
        def update():
            label.text = text
            
        # Schedule update on main thread
        asyncio.create_task(asyncio.to_thread(update))
        
    @staticmethod
    def update_chart(chart: ui.plotly, data: Any) -> None:
        """Update chart data from background thread."""
        def update():
            chart.update_figure(data)
            
        asyncio.create_task(asyncio.to_thread(update))
```

## Resource Management

### Context Manager for Threads
```python
class ManagedWorker:
    """Context manager for worker threads."""
    
    def __init__(self, worker_func: Callable, *args, **kwargs):
        self.worker_func = worker_func
        self.args = args
        self.kwargs = kwargs
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        
    def __enter__(self) -> 'ManagedWorker':
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
        
    def start(self) -> None:
        """Start the managed worker."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_with_stop_check,
            daemon=True
        )
        self._thread.start()
        
    def stop(self) -> None:
        """Stop the managed worker."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
            
    def _run_with_stop_check(self) -> None:
        """Run worker function with stop event checking."""
        try:
            self.worker_func(self._stop_event, *self.args, **self.kwargs)
        except Exception:
            logger.exception("Managed worker failed")
```

## Best Practices

### Thread Lifecycle Management
- Always use daemon threads for background tasks
- Implement proper stop mechanisms with timeouts
- Use context managers for automatic cleanup
- Handle exceptions within threads to prevent crashes

### Communication Patterns
- Use `queue.Queue` for thread-safe communication
- Limit queue sizes to prevent memory issues
- Use events for coordination between threads
- Avoid shared mutable state without proper locking