---
title: Configuration Patterns
inclusion: fileMatch
fileMatchPattern: 'src/core/config/**/*.py,config/*.json'
---

# Configuration Patterns

## Configuration Structure
- **JSON-based Config**: Application settings stored in JSON files
- **Hierarchical Settings**: Organize settings by component and scope
- **Environment Overrides**: Allow environment variables to override settings
- **Default Values**: Provide sensible defaults for all configuration options

## Configuration Files
- **Host Configuration**: SSH connection details and credentials
- **Scan Configuration**: Interface monitoring and data collection settings
- **Traffic Configuration**: Iperf testing parameters and network settings
- **UI Configuration**: Web interface settings and themes

## Validation Patterns
- **Pydantic Models**: Use Pydantic for configuration validation
- **Type Safety**: Ensure all configuration values are properly typed
- **Range Validation**: Validate numeric ranges and constraints
- **Dependency Validation**: Check for conflicting configuration options

## Path Handling
- **Pathlib Usage**: Use `pathlib.Path` for all file operations
- **Relative Paths**: Support relative paths in configuration
- **Path Resolution**: Resolve paths relative to configuration file location
- **Cross-platform**: Handle path differences across operating systems

## Configuration Loading
- **Lazy Loading**: Load configuration only when needed
- **Hot Reload**: Support configuration changes without restart
- **Error Handling**: Graceful handling of configuration errors
- **Backup Configuration**: Fallback to defaults on configuration errors

## Security Considerations
- **Credential Storage**: Secure storage of SSH credentials
- **File Permissions**: Appropriate permissions for configuration files
- **Environment Variables**: Use environment variables for sensitive data
- **Configuration Validation**: Validate configuration to prevent security issues
