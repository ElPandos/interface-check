# Interface Check - Development Guidelines

## Code Quality Standards

### Type Hints and Annotations
- **Comprehensive Type Hints**: All functions, methods, and class attributes must include type hints
- **Union Types**: Use `Union[Type1, Type2]` or `Type1 | Type2` for multiple possible types
- **Optional Types**: Use `Optional[Type]` or `Type | None` for nullable values
- **Generic Collections**: Specify container types like `List[str]`, `Dict[str, Any]`, `queue.Queue[Sample]`
- **TypedDict**: Use for structured dictionaries with known keys (e.g., `HostDict`, `RouteDict`)

### Documentation Standards
- **Docstrings**: All classes and public methods require Google-style docstrings
- **Inline Comments**: Complex logic sections include explanatory comments
- **Type Documentation**: Complex type definitions documented with purpose and usage
- **Error Context**: Exception handling includes descriptive error messages

### Error Handling Patterns
- **Try-Catch Blocks**: Comprehensive exception handling with specific error types
- **Logging Integration**: All exceptions logged with `logging.exception()` for stack traces
- **Graceful Degradation**: UI operations continue with user notifications on errors
- **Bounds Checking**: Array/list access protected with range validation
- **Resource Cleanup**: Proper cleanup in finally blocks or context managers

## Architectural Patterns

### Class Design
- **Dataclasses**: Use `@dataclass` for simple data containers with `frozen=True` for immutability
- **Private Methods**: Internal methods prefixed with underscore (`_method_name`)
- **Property Access**: Use properties for computed values and validation
- **Initialization**: Complex initialization in `__init__` with proper error handling

### UI Component Structure
- **Handler Pattern**: Separate UI logic from business logic using handler classes
- **Component Composition**: Build complex UI from reusable components
- **Event Callbacks**: Use lambda functions with closures for event handling
- **State Management**: Centralized state with clear update patterns

### Threading and Concurrency
- **Worker Threads**: Background tasks use daemon threads with proper lifecycle management
- **Thread Safety**: Queue-based communication between threads
- **Graceful Shutdown**: Stop events and join patterns for clean thread termination
- **Exception Isolation**: Thread exceptions don't crash main application

## Common Implementation Patterns

### Configuration Management
- **JSON-based Config**: Application settings stored in JSON files
- **Path Handling**: Use `pathlib.Path` for all file operations
- **Environment Variables**: Load from `.env` files using `python-dotenv`
- **Config Validation**: Validate configuration on load with error reporting

### Data Processing
- **Parser Classes**: Dedicated parser classes for structured data extraction
- **Regular Expressions**: Compiled regex patterns for performance
- **Data Validation**: Input sanitization and validation before processing
- **Structured Output**: Convert raw data to typed objects (ValueWithUnit pattern)

### SSH Connection Management
- **Connection Pooling**: Reuse SSH connections across components
- **Reconnection Logic**: Automatic reconnection with retry limits
- **Connection Status**: Visual indicators for connection health
- **Error Recovery**: Graceful handling of connection failures

### Logging Practices
- **Structured Logging**: Consistent log format with timestamps and context
- **Log Levels**: Appropriate use of DEBUG, INFO, WARNING, ERROR levels
- **Rotating Logs**: File rotation to prevent disk space issues
- **Performance Logging**: Debug timing information for operations

## UI Development Standards

### NiceGUI Patterns
- **Component Hierarchy**: Logical nesting of UI components with proper classes
- **Styling**: Consistent CSS classes using Tailwind-style utilities
- **Event Handling**: Proper event binding with error handling
- **Dynamic Updates**: Refresh patterns for live data updates

### User Experience
- **Loading States**: Visual feedback during long operations
- **Error Notifications**: User-friendly error messages with color coding
- **Input Validation**: Real-time validation with helpful error messages
- **Responsive Design**: Proper spacing and sizing for different screen sizes

### State Management
- **Component State**: Local state management within components
- **Global State**: Shared state through dependency injection
- **State Persistence**: Save/restore application state to files
- **State Synchronization**: Keep UI in sync with underlying data

## Testing and Quality Assurance

### Code Quality Tools
- **Ruff**: Comprehensive linting with ALL rules enabled
- **Black**: Code formatting with 120 character line length
- **MyPy**: Strict type checking with no untyped definitions
- **Pre-commit**: Automated quality checks on commit

### Development Workflow
- **Virtual Environments**: Use `uv` for dependency management
- **Reproducible Builds**: Lock file dependencies for consistency
- **Container Support**: Docker configuration for deployment
- **CI/CD**: GitHub Actions for automated testing and linting