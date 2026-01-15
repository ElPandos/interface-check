---
title:        NiceGUI Development Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# NiceGUI Development Patterns

## Purpose
Define patterns for NiceGUI web UI development in the interface-check project, including component architecture, theming, and state management.

## Core Patterns

### 1. Base Component Pattern
Abstract base classes for tabs and panels:

```python
class Base(ABC):
    def __init__(self, name: str, label: str, icon_name: str) -> None:
        self._name = name
        self._label = label
        self._icon_name = icon_name

    @abstractmethod
    def build(self) -> None:
        """Build the component."""

class BaseTab(Base):
    def build(self) -> None:
        with ui.column().classes("items-center gap-1"), ui.tab(self.name):
            self._icon = ui.icon(self.icon_name).props("size=24px")

class BasePanel(Base):
    def build(self) -> None:
        with ui.row().classes("items-center gap-2"):
            ui.icon(self.icon_name).props("size=24px")
            self._title = ui.label(self.label)
```

**Benefits**: Consistent component structure, reusable base functionality.

### 2. Tab-Panel Separation Pattern
Separate tab navigation from panel content:

```python
class HostTab(BaseTab):
    ICON_NAME = "home"
    
    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

class HostPanel(BasePanel):
    def __init__(self, cfg: Config, handler: HostHandler, build: bool = False):
        BasePanel.__init__(self, NAME, LABEL, HostTab.ICON_NAME)
        self._cfg = cfg
        self._handler = handler
        if build:
            self.build()
    
    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_content()
```

### 3. Handler Pattern
Separate business logic from UI components:

```python
class HostHandler:
    """Business logic for host management."""
    
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._connections: dict[str, SshConnection] = {}
    
    def connect(self, route: Route) -> bool:
        """Establish SSH connection."""
        ...
    
    def disconnect(self, host: str) -> None:
        """Close SSH connection."""
        ...

class HostPanel:
    def __init__(self, cfg: Config, handler: HostHandler):
        self._handler = handler
    
    def _on_connect_click(self) -> None:
        if self._handler.connect(self._selected_route):
            ui.notify("Connected", color="positive")
```

### 4. Theme System Pattern
Centralized theming with dataclasses:

```python
@dataclass(frozen=True)
class LightTheme:
    PRIMARY_BG = "bg-slate-50"
    SECONDARY_BG = "bg-stone-50"
    TEXT_PRIMARY = "text-slate-700"
    
    # Buttons
    PRIMARY_BUTTON = "bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg"
    DANGER_BUTTON = "bg-rose-500 hover:bg-rose-600 text-white px-4 py-2 rounded-lg"
    DISABLED_BUTTON = "bg-gray-100 text-gray-400 cursor-not-allowed px-4 py-2 rounded"
    
    # Cards
    CARD_BASE = "bg-white border border-stone-200 rounded-xl shadow-sm"

def apply_global_theme() -> None:
    """Apply global theme styles."""
    ui.add_head_html('''
        <style>
            body { font-family: 'Inter', sans-serif; }
            .q-tab { min-width: 80px; }
        </style>
    ''')
```

### 5. Lazy Build Pattern
Defer component building until needed:

```python
class HostTab(BaseTab):
    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

# Usage in Gui class
for tab_class in [LocalTab, HostTab, SlxTab]:
    tab = tab_class(build=True)  # Build immediately
    self._tab_content[tab.name] = tab
```

### 6. Dialog Pattern
Modal dialogs for user input:

```python
def _open_add_dialog(self) -> None:
    with (
        ui.dialog() as dialog,
        ui.card().classes("w-96 bg-white border shadow-lg"),
    ):
        ui.label("Add new host").classes("text-xl font-bold mb-6")
        
        ip_input = ui.input("IP address").classes("w-full mb-3").props("outlined")
        user_input = ui.input("Username").classes("w-full mb-3").props("outlined")
        pass_input = ui.input("Password", password=True).classes("w-full mb-6").props("outlined")
        
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).classes(BUTTON_STYLES["secondary"])
            ui.button("Add", on_click=lambda: self._add_host(dialog, ip_input, user_input, pass_input))
    
    dialog.open()
```

### 7. Notification Pattern
User feedback with ui.notify:

```python
def _save_cfg(self) -> None:
    try:
        self.config.save()
        ui.notify("Configuration saved", color="positive")
    except Exception:
        logger.exception("Error saving config")
        ui.notify("Failed to save configuration", color="negative")
```

### 8. Cache Invalidation Pattern
Manage UI state with cache:

```python
class HostContent:
    def __init__(self):
        self._remote_hosts_cache: list[dict] | None = None
        self._cache_dirty = True
    
    def _invalidate_cache(self) -> None:
        self._cache_dirty = True
        self._remote_hosts_cache = None
    
    def _get_remote_hosts(self) -> list[dict]:
        if self._cache_dirty or self._remote_hosts_cache is None:
            self._remote_hosts_cache = self._load_hosts()
            self._cache_dirty = False
        return self._remote_hosts_cache
```

## Layout Patterns

### Header with Tabs
```python
def _build_header(self) -> None:
    with ui.header().classes("row items-center justify-between"):
        with ui.tabs() as self._tabs:
            for tab_class in [LocalTab, HostTab, SlxTab]:
                tab = tab_class(build=True)
                self._tab_content[tab.name] = tab
        
        ui.button(on_click=self._drawer.toggle, icon="settings").props("flat color=white")
```

### Card-Based Sections
```python
def _build_hosts_section(self) -> None:
    with ui.card().classes("w-full bg-white border shadow-sm p-4"):
        with ui.row().classes("w-full items-center gap-2 mb-4"):
            ui.icon("computer", size="lg").classes("text-blue-600")
            ui.label("Hosts").classes("text-2xl font-semibold")
            ui.space()
            ui.button(icon="add", text="Add Host", on_click=self._open_add_dialog)
        
        self.table_container = ui.column().classes("w-full")
```

### Expandable Sections
```python
def _toggle_hosts(self) -> None:
    self.hosts_expanded = not self.hosts_expanded
    self._refresh_tables()
```

## Anti-Patterns to Avoid

### 1. Mixing Business Logic in UI
```python
# BAD
class HostPanel:
    def _on_connect(self):
        ssh = SshConnection(...)
        ssh.connect()
        result = ssh.exec_cmd("hostname")

# GOOD
class HostPanel:
    def _on_connect(self):
        if self._handler.connect(self._route):
            ui.notify("Connected")
```

### 2. Hardcoded Styles
```python
# BAD
ui.button("Save").classes("bg-blue-500 hover:bg-blue-600 text-white px-4 py-2")

# GOOD
ui.button("Save").classes(BUTTON_STYLES["primary"])
```

### 3. Missing Error Handling
```python
# BAD
def _save_cfg(self):
    self.config.save()

# GOOD
def _save_cfg(self):
    try:
        self.config.save()
        ui.notify("Saved", color="positive")
    except Exception:
        logger.exception("Save failed")
        ui.notify("Save failed", color="negative")
```

### 4. Direct State Mutation
```python
# BAD
self.hosts.append(new_host)
self._refresh_tables()

# GOOD
self.hosts.append(new_host)
self._invalidate_cache()
self._refresh_tables()
```

## Implementation Guidelines

### Component Lifecycle
1. Initialize with configuration and handlers
2. Call `build()` to create UI elements
3. Use `_refresh_*()` methods to update state
4. Clean up resources in disconnect/close handlers

### Styling Standards
- Use Tailwind CSS classes via `.classes()`
- Define reusable styles in theme dataclasses
- Use `.props()` for Quasar component properties
- Maintain consistent spacing with gap-* classes

### State Management
- Keep UI state in component instance variables
- Use cache invalidation for derived data
- Separate configuration from runtime state
- Use handlers for business logic

## Version History

- v1.0 (2026-01-14 00:00:00): Initial NiceGUI patterns based on codebase analysis
