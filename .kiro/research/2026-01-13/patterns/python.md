# Research Output – 2026-01-13 03:11 CET

## Original Prompt
> Research common python patterns and anti-patterns. Use the research file to create/update .kiro/steering/python_patterns.md

## Complete Response

### Python Patterns Research Summary

The research reveals significant evolution in Python patterns and anti-patterns, with emphasis on "Pythonic" code that leverages Python's unique features and conventions. Modern Python development focuses on readability, maintainability, and performance optimization.

#### Core Python Patterns (2024-2025)

**Creational Patterns:**
- **Singleton Pattern**: Ensures single instance creation with proper thread safety
- **Factory Method**: Creates objects without specifying exact classes
- **Abstract Factory**: Creates families of related objects
- **Builder Pattern**: Constructs complex objects step by step

**Structural Patterns:**
- **Adapter Pattern**: Allows incompatible interfaces to work together
- **Decorator Pattern**: Adds behavior to objects dynamically
- **Facade Pattern**: Provides simplified interface to complex subsystems
- **Composite Pattern**: Treats individual and composite objects uniformly

**Behavioral Patterns:**
- **Observer Pattern**: Defines one-to-many dependency between objects
- **Strategy Pattern**: Encapsulates algorithms and makes them interchangeable
- **Command Pattern**: Encapsulates requests as objects
- **Iterator Pattern**: Provides sequential access to elements

**Modern Python-Specific Patterns:**
- **Context Manager Pattern**: Using `with` statements for resource management
- **Generator Pattern**: Memory-efficient iteration with `yield`
- **Descriptor Pattern**: Customizing attribute access
- **Metaclass Pattern**: Controlling class creation

#### Critical Anti-Patterns to Avoid

**1. Mutable Default Arguments**
```python
# WRONG - Dangerous shared state
def add_item(item, items=[]):
    items.append(item)
    return items

# CORRECT - Safe initialization
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
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
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

**3. Performance Anti-Patterns**
```python
# WRONG - Inefficient string concatenation
result = ""
for item in items:
    result += str(item)

# CORRECT - Use join for string concatenation
result = "".join(str(item) for item in items)
```

**4. Import Anti-Patterns**
```python
# WRONG - Wildcard imports
from module import *

# CORRECT - Explicit imports
from module import specific_function, SpecificClass
```

**5. Loop Anti-Patterns**
```python
# WRONG - Manual indexing
for i in range(len(items)):
    print(i, items[i])

# CORRECT - Use enumerate
for i, item in enumerate(items):
    print(i, item)
```

#### Modern Python Best Practices (2025)

**Type Hints and Safety:**
- Use type hints consistently for better code documentation
- Leverage mypy for static type checking
- Handle mutable defaults with `None` and conditional initialization

**Async Programming:**
- Use `async`/`await` for I/O-bound operations
- Avoid blocking operations in async functions
- Leverage asyncio for concurrent programming

**Error Handling:**
- Use specific exception types
- Implement proper logging with structured data
- Follow fail-fast principles

**Performance Optimization:**
- Use list comprehensions over manual loops
- Leverage built-in functions like `map()`, `filter()`, `reduce()`
- Profile code before optimizing

## Key Findings
- **Mutable default arguments** remain the most dangerous Python anti-pattern, causing shared state bugs
- **Exception handling anti-patterns** like bare except clauses and exception swallowing are still prevalent  
- **Performance anti-patterns** including inefficient list operations and string concatenation in loops continue to impact applications
- **Modern type hint usage** is essential, with Any overuse defeating the purpose of type safety
- **Async/await anti-patterns** like blocking operations in async functions are becoming more common as async adoption grows

## Sources & References
- [Improving Python Code: Learning "Pythonic" Writing from Anti-Patterns](https://morinokabu.com/2025/12/04/improving-python-code-learning-pythonic-writing-from-anti-patterns/) — Pythonic writing principles and anti-pattern recognition
- [Common Anti-Patterns in Python: Avoiding Pitfalls for Better Code Quality](https://softwarepatternslexicon.com/python/anti-patterns/common-anti-patterns-in-python/) — Comprehensive anti-pattern catalog
- [Python Code Review Checklist: Pythonic Code and Best Practices](https://pullpanda.io/blog/python-code-review-checklist) — Code review guidelines and common mistakes
- [18 Common Python Anti-Patterns I Wish I Had Known Before](https://readmedium.com/18-common-python-anti-patterns-i-wish-i-had-known-before-44d983805f0f) — Practical anti-pattern examples
- [Anti-Patterns in Python](https://useful.codes/anti-patterns-in-python/) — Modern anti-pattern analysis

## Tools & Methods Used
- web_search: "Python patterns anti-patterns 2024 2025 best practices common mistakes"
- web_search: "Python design patterns 2025 creational structural behavioral modern patterns"
- web_search: "Python mutable default arguments exception handling performance anti-patterns 2025"

## Metadata
- Generated: 2026-01-13T03:11:25+01:00
- Model: Claude 3.5 Sonnet
- Tags: python, patterns, anti-patterns, best-practices, code-quality
- Confidence: High - based on current industry research and established Python conventions
- Version: 1

## Limitations & Confidence Notes
- Data current as of January 2025
- Focus on common patterns and anti-patterns, not exhaustive coverage
- Next steps: Consider framework-specific patterns (Django, FastAPI, etc.)
