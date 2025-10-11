# NiceGUI Development Patterns

## Component Structure
- **Context managers**: Use `with ui.component():` for proper nesting
- **Classes**: CSS classes using Tailwind-style utilities
- **Event handling**: Lambda functions with proper closures
- **State management**: Reactive updates with `ui.refreshable`

## Common Patterns
```python
# Proper component nesting
with ui.card().classes("w-full p-4"):
    with ui.row().classes("items-center gap-4"):
        ui.label("Status:")
        ui.badge("Connected", color="positive")

# Event handling with closures
def create_button_handler(item_id: str):
    return lambda: handle_click(item_id)

ui.button("Click", on_click=create_button_handler("item1"))

# Refreshable components for dynamic updates
@ui.refreshable
def status_display():
    if ssh_connection.is_connected():
        ui.badge("Connected", color="positive")
    else:
        ui.badge("Disconnected", color="negative")
```

## Styling Guidelines
- **Consistent spacing**: Use gap-* classes for spacing
- **Color scheme**: Follow established color patterns
- **Responsive design**: Use w-full, flex classes appropriately
- **Custom CSS**: Add via `ui.add_head_html()` for complex styling

## Tab Implementation
- **Tab creation**: Use `ui.tab(name)` with consistent naming
- **Panel content**: Use `ui.tab_panel(name)` with matching names
- **Icons**: Consistent icon usage with proper sizing
- **State persistence**: Save tab state in configuration