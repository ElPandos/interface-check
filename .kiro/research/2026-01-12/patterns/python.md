# Research Output – 2026-01-12 20:33 CET

## Original Prompt
> Research best python patterns. Use the research file to create a .kiro/steering/python_patterns.md file

## Complete Response

# Python Patterns

Python development has evolved significantly with modern language features and best practices. This comprehensive guide covers essential patterns for building maintainable, readable, and robust Python applications.

## Core Design Patterns

### 1. Creational Patterns

#### Factory Pattern
```python
from abc import ABC, abstractmethod
from typing import Protocol

class PaymentProcessor(Protocol):
    def process_payment(self, amount: float) -> bool: ...

class CreditCardProcessor:
    def process_payment(self, amount: float) -> bool:
        return True

class PayPalProcessor:
    def process_payment(self, amount: float) -> bool:
        return True

class PaymentFactory:
    @staticmethod
    def create_processor(payment_type: str) -> PaymentProcessor:
        processors = {
            'credit_card': CreditCardProcessor,
            'paypal': PayPalProcessor,
        }
        processor_class = processors.get(payment_type)
        if not processor_class:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return processor_class()
```

#### Singleton Pattern
```python
from typing import Optional

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DatabaseConnection':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.connection = self._create_connection()
            self._initialized = True
    
    def _create_connection(self):
        # Expensive connection setup
        return "database_connection"
```

### 2. Behavioral Patterns

#### Observer Pattern
```python
from typing import List, Protocol
from abc import ABC, abstractmethod

class Observer(Protocol):
    def update(self, message: str) -> None: ...

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    def notify(self, message: str) -> None:
        for observer in self._observers:
            observer.update(message)

class EmailNotifier:
    def update(self, message: str) -> None:
        print(f"Email: {message}")

class SMSNotifier:
    def update(self, message: str) -> None:
        print(f"SMS: {message}")
```

#### Strategy Pattern
```python
from abc import ABC, abstractmethod
from typing import List

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: List[int]) -> List[int]: ...

class QuickSort(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        if len(data) <= 1:
            return data
        pivot = data[len(data) // 2]
        left = [x for x in data if x < pivot]
        middle = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + middle + self.sort(right)

class BubbleSort(SortStrategy):
    def sort(self, data: List[int]) -> List[int]:
        data = data.copy()
        n = len(data)
        for i in range(n):
            for j in range(0, n - i - 1):
                if data[j] > data[j + 1]:
                    data[j], data[j + 1] = data[j + 1], data[j]
        return data

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: SortStrategy) -> None:
        self._strategy = strategy
    
    def sort(self, data: List[int]) -> List[int]:
        return self._strategy.sort(data)
```

## SOLID Principles Implementation

### 1. Single Responsibility Principle (SRP)
```python
# Bad: Multiple responsibilities
class UserManager:
    def create_user(self, user_data): ...
    def send_welcome_email(self, user): ...
    def log_creation(self, user): ...

# Good: Separated responsibilities
class UserService:
    def __init__(self, repository, email_service, logger):
        self.repository = repository
        self.email_service = email_service
        self.logger = logger
    
    def create_user(self, user_data):
        user = User(**user_data)
        self.repository.save(user)
        self.email_service.send_welcome(user)
        self.logger.info(f"User created: {user.id}")
        return user
```

### 2. Open/Closed Principle (OCP)
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return 3.14159 * self.radius ** 2

class AreaCalculator:
    def total_area(self, shapes: List[Shape]) -> float:
        return sum(shape.area() for shape in shapes)
```

### 3. Dependency Inversion Principle (DIP)
```python
from typing import Protocol

class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...

class SMTPEmailSender:
    def send(self, to: str, subject: str, body: str) -> None:
        print(f"SMTP: Sending to {to}")

class UserRegistrationService:
    def __init__(self, email_sender: EmailSender):
        self.email_sender = email_sender
    
    def register(self, email: str, name: str):
        # Registration logic
        self.email_sender.send(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!"
        )
```

## Modern Python Data Patterns

### 1. Dataclasses vs Pydantic
```python
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Dataclass - Simple, fast, built-in
@dataclass
class UserDataclass:
    name: str
    email: str
    age: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

# Pydantic - Validation, serialization, API integration
class UserPydantic(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(0, ge=0, le=150)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('name')
    def name_must_not_contain_numbers(cls, v):
        if any(char.isdigit() for char in v):
            raise ValueError('Name cannot contain numbers')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 2. Type Hints and Protocols
```python
from typing import Protocol, runtime_checkable, TypeVar, Generic
from abc import abstractmethod

T = TypeVar('T')

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> 'Serializable': ...

class Repository(Protocol, Generic[T]):
    def save(self, entity: T) -> T: ...
    def get_by_id(self, id: str) -> Optional[T]: ...
    def delete(self, id: str) -> bool: ...

class UserRepository:
    def save(self, user: User) -> User:
        # Implementation
        return user
    
    def get_by_id(self, id: str) -> Optional[User]:
        # Implementation
        return None
    
    def delete(self, id: str) -> bool:
        # Implementation
        return True

# Type checking works
def process_serializable(obj: Serializable) -> dict:
    return obj.to_dict()

def use_repository(repo: Repository[User], user: User):
    saved_user = repo.save(user)
    return saved_user
```

## Structural Pattern Matching (Python 3.10+)

### 1. Basic Pattern Matching
```python
def process_data(data):
    match data:
        case int() if data > 0:
            return f"Positive integer: {data}"
        case int() if data < 0:
            return f"Negative integer: {data}"
        case 0:
            return "Zero"
        case str() if len(data) > 0:
            return f"Non-empty string: {data}"
        case []:
            return "Empty list"
        case [x] if isinstance(x, int):
            return f"Single integer list: {x}"
        case [x, y]:
            return f"Two-element list: {x}, {y}"
        case {"name": str(name), "age": int(age)}:
            return f"Person: {name}, age {age}"
        case _:
            return "Unknown data type"
```

### 2. Advanced Pattern Matching with Classes
```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

@dataclass
class Circle:
    center: Point
    radius: float

@dataclass
class Rectangle:
    top_left: Point
    bottom_right: Point

def describe_shape(shape):
    match shape:
        case Circle(Point(0, 0), radius):
            return f"Circle at origin with radius {radius}"
        case Circle(center, radius) if radius > 10:
            return f"Large circle at {center} with radius {radius}"
        case Circle(center, radius):
            return f"Small circle at {center} with radius {radius}"
        case Rectangle(Point(x1, y1), Point(x2, y2)) if x1 == x2 or y1 == y2:
            return "Degenerate rectangle (line)"
        case Rectangle(top_left, bottom_right):
            return f"Rectangle from {top_left} to {bottom_right}"
        case _:
            return "Unknown shape"
```

## Async Programming Patterns

### 1. Async Context Managers
```python
import asyncio
import aiohttp
from typing import AsyncContextManager

class AsyncDatabaseConnection:
    async def __aenter__(self):
        self.connection = await self._connect()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._disconnect()
    
    async def _connect(self):
        await asyncio.sleep(0.1)  # Simulate connection
        return "database_connection"
    
    async def _disconnect(self):
        await asyncio.sleep(0.1)  # Simulate disconnection

# Usage
async def database_operation():
    async with AsyncDatabaseConnection() as conn:
        # Use connection
        return "result"
```

### 2. Async Generators and Iterators
```python
import asyncio
from typing import AsyncGenerator, AsyncIterator

async def async_range(start: int, stop: int) -> AsyncGenerator[int, None]:
    for i in range(start, stop):
        await asyncio.sleep(0.1)  # Simulate async work
        yield i

class AsyncFileReader:
    def __init__(self, filename: str):
        self.filename = filename
    
    def __aiter__(self) -> AsyncIterator[str]:
        return self
    
    async def __anext__(self) -> str:
        # Simulate reading file line by line
        await asyncio.sleep(0.1)
        # In real implementation, read actual file
        raise StopAsyncIteration

# Usage
async def process_data():
    async for number in async_range(0, 5):
        print(f"Processing {number}")
    
    async for line in AsyncFileReader("data.txt"):
        print(f"Line: {line}")
```

### 3. Async Patterns with Error Handling
```python
import asyncio
from typing import List, Tuple, Any

async def fetch_with_retry(url: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            # Simulate HTTP request
            await asyncio.sleep(0.1)
            if attempt < 2:  # Simulate failures
                raise aiohttp.ClientError("Connection failed")
            return f"Data from {url}"
        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def gather_with_error_handling(urls: List[str]) -> List[Tuple[str, Any]]:
    async def safe_fetch(url: str) -> Tuple[str, Any]:
        try:
            result = await fetch_with_retry(url)
            return url, result
        except Exception as e:
            return url, e
    
    tasks = [safe_fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## Functional Programming Patterns

### 1. Immutable Data Structures
```python
from dataclasses import dataclass
from typing import List, Tuple
import operator
from functools import reduce

@dataclass(frozen=True)
class Point:
    x: float
    y: float
    
    def move(self, dx: float, dy: float) -> 'Point':
        return Point(self.x + dx, self.y + dy)
    
    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

@dataclass(frozen=True)
class ImmutableList:
    items: Tuple[Any, ...]
    
    def __init__(self, items: List[Any]):
        object.__setattr__(self, 'items', tuple(items))
    
    def append(self, item: Any) -> 'ImmutableList':
        return ImmutableList(list(self.items) + [item])
    
    def filter(self, predicate) -> 'ImmutableList':
        return ImmutableList([item for item in self.items if predicate(item)])
    
    def map(self, func) -> 'ImmutableList':
        return ImmutableList([func(item) for item in self.items])
```

### 2. Higher-Order Functions
```python
from typing import Callable, TypeVar, List, Optional
from functools import partial, reduce

T = TypeVar('T')
U = TypeVar('U')

def compose(*functions):
    """Compose functions right to left."""
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)

def pipe(value, *functions):
    """Apply functions left to right."""
    return reduce(lambda acc, func: func(acc), functions, value)

def curry(func: Callable) -> Callable:
    """Convert function to curried form."""
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= func.__code__.co_argcount:
            return func(*args, **kwargs)
        return partial(func, *args, **kwargs)
    return curried

# Usage examples
@curry
def add_three_numbers(a: int, b: int, c: int) -> int:
    return a + b + c

# Partial application
add_five = add_three_numbers(2)(3)
result = add_five(5)  # 10

# Function composition
def double(x: int) -> int:
    return x * 2

def add_one(x: int) -> int:
    return x + 1

def square(x: int) -> int:
    return x ** 2

# Compose: square(add_one(double(x)))
composed = compose(square, add_one, double)
result = composed(3)  # square(add_one(double(3))) = square(7) = 49

# Pipe: more readable left-to-right
result = pipe(3, double, add_one, square)  # 49
```

## Error Handling Patterns

### 1. Result Type Pattern
```python
from typing import TypeVar, Generic, Union, Callable
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Ok(Generic[T]):
    value: T

@dataclass
class Err(Generic[E]):
    error: E

Result = Union[Ok[T], Err[E]]

def safe_divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

def map_result(result: Result[T, E], func: Callable[[T], U]) -> Result[U, E]:
    if isinstance(result, Ok):
        return Ok(func(result.value))
    return result

def bind_result(result: Result[T, E], func: Callable[[T], Result[U, E]]) -> Result[U, E]:
    if isinstance(result, Ok):
        return func(result.value)
    return result

# Usage
result = safe_divide(10, 2)
if isinstance(result, Ok):
    print(f"Result: {result.value}")
else:
    print(f"Error: {result.error}")

# Chaining operations
final_result = bind_result(
    safe_divide(10, 2),
    lambda x: safe_divide(x, 2)
)
```

### 2. Exception Context Managers
```python
import logging
from contextlib import contextmanager
from typing import Generator, Type, Optional

@contextmanager
def handle_exceptions(
    *exception_types: Type[Exception],
    logger: Optional[logging.Logger] = None,
    reraise: bool = False
) -> Generator[None, None, None]:
    try:
        yield
    except exception_types as e:
        if logger:
            logger.error(f"Exception handled: {e}")
        if reraise:
            raise

# Usage
with handle_exceptions(ValueError, TypeError, logger=logging.getLogger()):
    # Code that might raise ValueError or TypeError
    risky_operation()
```

## Performance Patterns

### 1. Caching and Memoization
```python
import functools
from typing import Dict, Any, Callable
import time

class LRUCache:
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self.cache: Dict[Any, Any] = {}
        self.access_order: List[Any] = []
    
    def get(self, key: Any) -> Any:
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.maxsize:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = value
        self.access_order.append(key)

def timed_lru_cache(seconds: int, maxsize: int = 128):
    def decorator(func: Callable) -> Callable:
        cache = {}
        times = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            if key in cache and now - times[key] < seconds:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            times[key] = now
            
            # Clean old entries
            if len(cache) > maxsize:
                oldest_key = min(times.keys(), key=lambda k: times[k])
                del cache[oldest_key]
                del times[oldest_key]
            
            return result
        return wrapper
    return decorator

# Usage
@timed_lru_cache(seconds=60, maxsize=100)
def expensive_computation(n: int) -> int:
    time.sleep(1)  # Simulate expensive operation
    return n ** 2
```

### 2. Generator Patterns for Memory Efficiency
```python
from typing import Iterator, Generator
import csv

def read_large_file(filename: str) -> Generator[str, None, None]:
    """Memory-efficient file reading."""
    with open(filename, 'r') as file:
        for line in file:
            yield line.strip()

def process_csv_chunks(filename: str, chunk_size: int = 1000) -> Generator[List[dict], None, None]:
    """Process CSV in chunks to manage memory."""
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

def fibonacci_generator() -> Generator[int, None, None]:
    """Infinite Fibonacci sequence generator."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Usage
for i, fib in enumerate(fibonacci_generator()):
    if i >= 10:
        break
    print(fib)
```

## Context Managers and Resource Management

### 1. Custom Context Managers
```python
import sqlite3
from contextlib import contextmanager
from typing import Generator

@contextmanager
def database_transaction(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions with automatic rollback."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

class FileManager:
    """Context manager class for file operations."""
    def __init__(self, filename: str, mode: str = 'r'):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        # Return False to propagate exceptions
        return False

# Usage
with database_transaction("example.db") as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))

with FileManager("data.txt", "w") as f:
    f.write("Hello, World!")
```

## Decorator Patterns

### 1. Advanced Decorators
```python
import functools
import time
from typing import Callable, Any, Dict
import logging

def timing_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def retry_decorator(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def validate_types(**type_hints):
    """Decorator to validate function argument types."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate types
            for param_name, expected_type in type_hints.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"Argument '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@timing_decorator
@retry_decorator(max_attempts=3, delay=0.5)
@validate_types(x=int, y=int)
def add_numbers(x: int, y: int) -> int:
    if x < 0 or y < 0:
        raise ValueError("Numbers must be positive")
    return x + y
```

## Key Findings

- **Modern Python emphasizes type safety** through protocols, type hints, and static analysis tools
- **Structural pattern matching** (Python 3.10+) provides powerful data destructuring capabilities
- **Dataclasses and Pydantic** offer different approaches to data modeling with distinct use cases
- **Async patterns** are essential for I/O-bound applications and concurrent programming
- **Functional programming concepts** like immutability and higher-order functions improve code reliability
- **Context managers** provide elegant resource management and error handling
- **SOLID principles** remain fundamental for maintainable object-oriented design

## Sources & References

- [Comprehensive Guide to Design Patterns in Python](https://joseph-fox.co.uk/tech/design-patterns-in-python) — Detailed explanations and code examples
- [Python Best Practices and Coding Standards](https://cursorrules.org/article/python-cursor-mdc-file) — Comprehensive development standards
- [Classic Design Patterns in Python](https://lab.abilian.com/Tech/Python/OOP/Classic%20Design%20Patterns%20in%20Python/) — Modern perspective on surviving patterns
- [Statically Typed Functional Programming with Python 3.12](https://wickstrom.tech/2024-05-23-statically-typed-functional-programming-python-312.html) — Advanced typing and pattern matching
- [Structural Pattern Matching in Python](https://realpython.com/structural-pattern-matching/) — Comprehensive pattern matching guide
- [Dependency Injection in Python](https://www.glukhov.org/post/2025/12/dependency-injection-in-python/) — Modern DI approaches
- [Python Design Patterns for Clean Architecture](https://www.glukhov.org/post/2025/11/python-design-patterns-for-clean-architecture/) — Architectural patterns

## Tools & Methods Used

- web_search: "Python design patterns 2024 2025 modern best practices"
- web_search: "Python functional programming patterns dataclasses pydantic async patterns 2024"
- web_search: "Python SOLID principles dependency injection context managers protocols 2024"
- web_search: "Python modern patterns structural pattern matching match case protocols typing 2024"

## Metadata

- Generated: 2026-01-12T20:33:22+01:00
- Model: Claude 3.5 Sonnet
- Session ID: N/A
- Tool calls total: 4
- Approximate duration: ~3 minutes

## Limitations & Confidence Notes

- Data current as of January 2026 – Python ecosystem evolves rapidly
- Examples focus on Python 3.10+ features; older versions may not support all patterns
- Performance characteristics may vary based on specific use cases and data sizes
- Recommended next steps: Implement patterns incrementally, profile performance impact, establish team coding standards
