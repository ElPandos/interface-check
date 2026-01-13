# Research Output – 2026-01-13 01:49 CET

## Original Prompt
> Research common python patterns and anti-patterns. Use the research file to create/update .kiro/steering/python_patterns.md

## Complete Response

Based on current research from 2025, Python patterns and anti-patterns have evolved significantly with modern development practices. Here's a comprehensive analysis:

### Core Python Patterns (2025)

**1. Context Managers**
- Essential for resource management (files, database connections, locks)
- Custom context managers using `__enter__` and `__exit__` methods
- `contextlib` module for creating context managers with decorators

**2. Iterator and Generator Patterns**
- Memory-efficient data processing with generators
- `yield` for lazy evaluation and streaming data
- Generator expressions for concise iteration

**3. Decorator Patterns**
- Function and class decorators for cross-cutting concerns
- `functools.wraps` for preserving metadata
- Parameterized decorators for flexible behavior modification

**4. Pythonic Data Structures**
- List comprehensions and dictionary comprehensions
- `collections` module (defaultdict, Counter, namedtuple)
- Dataclasses for structured data with minimal boilerplate

**5. Error Handling Patterns**
- Specific exception handling with multiple except blocks
- Custom exceptions for domain-specific errors
- EAFP (Easier to Ask for Forgiveness than Permission) approach

### Critical Anti-Patterns to Avoid (2025)

**1. Mutable Default Arguments**
```python
# WRONG - Creates shared state bugs
def append_item(item, target=[]):
    target.append(item)
    return target

# CORRECT - Use None and create new list
def append_item(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target
```

**2. Exception Handling Anti-Patterns**
```python
# WRONG - Bare except catches everything
try:
    risky_operation()
except:
    pass

# CORRECT - Specific exception handling
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
```

**3. Performance Anti-Patterns**
```python
# WRONG - Inefficient list operations
result = []
for item in large_list:
    if condition(item):
        result.append(transform(item))

# CORRECT - List comprehension
result = [transform(item) for item in large_list if condition(item)]
```

**4. String Concatenation in Loops**
```python
# WRONG - Creates new string objects repeatedly
result = ""
for item in items:
    result += str(item)

# CORRECT - Use join for multiple concatenations
result = "".join(str(item) for item in items)
```

**5. Global Variables**
- Avoid global state that creates hidden dependencies
- Use dependency injection or configuration objects instead
- Global constants are acceptable when properly named (ALL_CAPS)

### Modern Python Patterns (2025)

**1. Type Hints and Static Analysis**
```python
from typing import List, Optional, Dict, Any

def process_data(items: List[Dict[str, Any]]) -> Optional[str]:
    if not items:
        return None
    return str(len(items))
```

**2. Async/Await Patterns**
```python
import asyncio
import aiohttp

async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        return await response.json()
```

**3. Dataclasses and Pydantic Models**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    age: Optional[int] = None
```

**4. Pathlib for File Operations**
```python
from pathlib import Path

# Modern approach
config_file = Path("config") / "settings.json"
if config_file.exists():
    content = config_file.read_text()
```

### Anti-Patterns in Modern Context (2025)

**1. Import Anti-Patterns**
```python
# WRONG - Wildcard imports pollute namespace
from module import *

# WRONG - Importing unused modules
import sys, os, json, requests  # Only import what you use

# CORRECT - Specific imports
from pathlib import Path
from typing import List, Dict
```

**2. Any Type Overuse**
```python
# WRONG - Defeats purpose of type hints
def process(data: Any) -> Any:
    return data

# CORRECT - Specific types
def process(data: Dict[str, str]) -> List[str]:
    return list(data.values())
```

**3. Async/Await Anti-Patterns**
```python
# WRONG - Blocking operations in async functions
async def bad_async():
    time.sleep(1)  # Blocks event loop
    return "done"

# CORRECT - Use async alternatives
async def good_async():
    await asyncio.sleep(1)  # Non-blocking
    return "done"
```

**4. Resource Management Anti-Patterns**
```python
# WRONG - Manual resource management
file = open("data.txt")
data = file.read()
file.close()  # Might not execute if exception occurs

# CORRECT - Context manager
with open("data.txt") as file:
    data = file.read()
```

**5. Loop Anti-Patterns**
```python
# WRONG - Manual indexing when not needed
for i in range(len(items)):
    print(items[i])

# CORRECT - Direct iteration
for item in items:
    print(item)

# CORRECT - When index is needed
for i, item in enumerate(items):
    print(f"{i}: {item}")
```

### Testing Anti-Patterns

**1. Test Isolation Issues**
```python
# WRONG - Tests depend on each other
class TestUser:
    user = None
    
    def test_create_user(self):
        self.user = User("John")
        assert self.user.name == "John"
    
    def test_update_user(self):
        self.user.name = "Jane"  # Depends on previous test
        assert self.user.name == "Jane"
```

**2. Overly Complex Test Setup**
```python
# WRONG - Complex setup in each test
def test_user_creation():
    db = Database()
    db.connect()
    db.create_tables()
    user_service = UserService(db)
    # ... actual test logic

# CORRECT - Use fixtures and dependency injection
@pytest.fixture
def user_service():
    return UserService(mock_database)

def test_user_creation(user_service):
    # ... actual test logic
```

## Key Findings

- **Mutable default arguments** remain the most dangerous Python anti-pattern, causing shared state bugs
- **Exception handling anti-patterns** like bare except clauses and exception swallowing are still prevalent
- **Performance anti-patterns** including inefficient list operations and string concatenation in loops continue to impact applications
- **Modern type hint usage** is essential, with Any overuse defeating the purpose of type safety
- **Async/await anti-patterns** like blocking operations in async functions are becoming more common as async adoption grows

## Sources & References

- [Improving Python Code: Learning "Pythonic" Writing from Anti-Patterns](https://morinokabu.com/2025/12/04/improving-python-code-learning-pythonic-writing-from-anti-patterns/) — Modern Pythonic practices and anti-pattern recognition
- [Common Anti-Patterns in Python: Avoiding Pitfalls for Better Code Quality](https://softwarepatternslexicon.com/python/anti-patterns/common-anti-patterns-in-python/) — Comprehensive anti-pattern analysis
- [Python Code Review Checklist: Pythonic Code and Best Practices](https://pullpanda.io/blog/python-code-review-checklist) — Code review best practices and common mistakes
- [18 Common Python Anti-Patterns I Wish I Had Known Before](https://readmedium.com/18-common-python-anti-patterns-i-wish-i-had-known-before-44d983805f0f) — Practical anti-pattern examples with solutions
- [Anti-Patterns in Python](https://useful.codes/anti-patterns-in-python/) — Modern anti-pattern identification and refactoring strategies

## Tools & Methods Used

- web_search: "Python patterns anti-patterns 2024 2025 best practices common mistakes"
- web_fetch: https://useful.codes/anti-patterns-in-python/ → anti-patterns common mistakes mutable default arguments exception handling
- web_fetch: https://readmedium.com/18-common-python-anti-patterns-i-wish-i-had-known-before-44d983805f0f → mutable default arguments exception handling performance anti-patterns

## Metadata

- Generated: 2026-01-13T01:49:26+01:00
- Model: Claude 3.5 Sonnet
- Tags: python, patterns, anti-patterns, best-practices, code-quality
- Confidence: High - Based on current 2025 research and established Python community practices
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2025
- Focus on common patterns rather than advanced architectural patterns
- Anti-patterns based on community consensus and practical experience
- Next steps: Consider framework-specific patterns (Django, FastAPI, etc.)
