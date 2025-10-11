# Architecture Patterns

## Tab-Panel Architecture
- **Tabs**: UI navigation elements in header (`src/ui/tabs/`)
- **Panels**: Content containers in body (`src/ui/tabs/` with Panel suffix)
- **Base Classes**: Inherit from `BaseTab` and `BasePanel`
- **Naming**: Consistent naming pattern (e.g., `HostTab`, `HostPanel`)

## SSH Connection Management
- **Shared Instance**: Single `SshConnection` passed to all components
- **Context Manager**: Use `with ssh_connection:` for automatic cleanup
- **Connection Status**: Check `is_connected()` before operations
- **Error Handling**: Graceful degradation on connection failures

## UI Component Structure
```python
# Tab definition
class ExampleTab(BaseTab):
    def __init__(self, build: bool = False):
        super().__init__("example", "Example", "icon_name")
        if build:
            self.build()

# Panel implementation  
class ExamplePanel(BasePanel):
    def __init__(self, build: bool, app_config: AppConfig, ssh_connection: SshConnection):
        super().__init__("example", "Example")
        self._app_config = app_config
        self._ssh_connection = ssh_connection
        if build:
            self.build()
```

## Handler Pattern
- Separate business logic from UI components
- Handlers in `src/ui/handlers/`
- Pass dependencies through constructor injection
- Use type hints for all handler methods