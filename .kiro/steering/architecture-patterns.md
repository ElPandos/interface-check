---
title: Architecture Patterns
inclusion: always
---

# Architecture Patterns

## Class Design
- **Dataclasses**: Use `@dataclass` for simple data containers with `frozen=True` for immutability
- **Private Methods**: Internal methods prefixed with underscore (`_method_name`)
- **Property Access**: Use properties for computed values and validation
- **Initialization**: Complex initialization in `__init__` with proper error handling

## Threading and Concurrency
- **Worker Threads**: Background tasks use daemon threads with proper lifecycle management
- **Thread Safety**: Queue-based communication between threads
- **Graceful Shutdown**: Stop events and join patterns for clean thread termination
- **Exception Isolation**: Thread exceptions don't crash main application

## Configuration Management
- **JSON-based Config**: Application settings stored in JSON files
- **Path Handling**: Use `pathlib.Path` for all file operations
- **Environment Variables**: Load from `.env` files using `python-dotenv`
- **Config Validation**: Validate configuration on load with error reporting

## Data Processing
- **Parser Classes**: Dedicated parser classes for structured data extraction
- **Regular Expressions**: Compiled regex patterns for performance
- **Data Validation**: Input sanitization and validation before processing
- **Structured Output**: Convert raw data to typed objects (ValueWithUnit pattern)

## Logging Practices
- **Structured Logging**: Consistent log format with timestamps and context
- **Log Levels**: Appropriate use of DEBUG, INFO, WARNING, ERROR levels
- **Rotating Logs**: File rotation to prevent disk space issues
- **Performance Logging**: Debug timing information for operations
