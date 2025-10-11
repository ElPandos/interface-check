# Development Workflow

## Environment Setup
```bash
# Initial setup
uv sync
source .venv/bin/activate

# Development commands
uv run main.py              # Run application
uv run ruff check . --fix   # Lint and fix
uv run mypy .              # Type checking
uv run pytest --cov=src   # Run tests with coverage
```

## Code Development Process
1. **Feature Planning**: Review TODO.txt and project requirements
2. **Implementation**: Follow architecture patterns and type safety rules
3. **Testing**: Write tests for new functionality
4. **Quality Check**: Run linting, type checking, and tests
5. **Documentation**: Update docstrings and comments

## Common Development Scenarios

### Adding New Network Tool Support
1. Create parser in `src/utils/commands.py`
2. Add data models in `src/models/`
3. Create tab and panel in `src/ui/tabs/`
4. Update GUI to include new tab
5. Add tests for parsing logic

### Adding New UI Components
1. Follow NiceGUI patterns from project rules
2. Use consistent styling and event handling
3. Implement proper error handling and loading states
4. Test component behavior and responsiveness

### SSH Operation Implementation
1. Use shared SSH connection instance
2. Implement proper error handling and timeouts
3. Add logging for debugging
4. Test connection lifecycle management

## Troubleshooting Common Issues

### SSH Connection Problems
- Check connection status before operations
- Implement reconnection logic with backoff
- Log connection attempts and failures
- Verify jump host and target configurations

### UI Performance Issues
- Profile component rendering times
- Implement virtual scrolling for large datasets
- Use debouncing for user input
- Optimize chart update frequencies

### Memory Usage
- Monitor memory usage with pympler
- Implement circular buffers for time series data
- Clean up old data points regularly
- Use appropriate data structures (__slots__, deque)

## Integration Patterns
For detailed integration patterns, see:
- Network command parsing: `.amazonq/rule-details/project/network_command_parsing.md`
- Threading patterns: `.amazonq/rule-details/project/threading_patterns.md`
- Performance optimization: `.amazonq/rule-details/project/performance_profiling.md`