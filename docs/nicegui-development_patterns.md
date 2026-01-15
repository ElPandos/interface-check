---
title:        Nicegui Development Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15
status:       active
---

# Nicegui Development Patterns

## Core Principles

### 1. Backend-First Philosophy
NiceGUI operates with a backend-first architecture where all UI logic lives in Python. The framework handles web details (Vue/Quasar frontend, socket.io communication) automatically.

### 2. Context Manager Hierarchy
Elements nest using Python's `with` statement, mirroring HTML structure. This provides intuitive parent-child relationships and automatic cleanup.

### 3. Reactive State Management
State changes trigger UI updates automatically through bindings and refreshables. Avoid manual DOM manipulation.

### 4. Per-Client Isolation
Each client connection maintains separate state through `@ui.page` decorators and `ui.context`. Global data requires explicit sharing patterns.

### 5. Async-First Design
NiceGUI is built on FastAPI with full async support. Use `async def` for I/O operations and background tasks.

## Essential Patterns

### State Management

#### Global Data with Per-Client UI State
**Pattern**: Move `@ui.refreshable` outside page functions to track all clients while maintaining per-client state.

```python
# Global shared data
data = []

def update_data(item):
    data.append(item)
    display.refresh()  # Updates all connected clients

@ui.refreshable
def display(ui_state: dict):
    """Refreshable tracks all clients, ui_state is per-client"""
    for item in data:
        ui.label(item.upper() if ui_state['uppercase'] else item.lower())

@ui.page('/')
def main():
    ui_state = {'uppercase': False}  # Per-client state
    display(ui_state)
    ui.switch('Uppercase', on_change=display.refresh).bind_value_to(ui_state, 'uppercase')
```

**Key Insight**: The refreshable keeps a reference to `ui_state`. When `refresh()` is called, each client reads updated attributes from their own `ui_state` object.

#### Using app.storage for Persistence
```python
from nicegui import app, ui

@ui.page('/')
def main():
    # User-specific storage (persists across sessions)
    app.storage.user['preferences'] = {'theme': 'dark'}
    
    # General storage (shared across all users)
    app.storage.general['visit_count'] = app.storage.general.get('visit_count', 0) + 1
    
    # Browser storage (client-side, survives page reloads)
    app.storage.browser['session_id'] = generate_id()
```

### Async Operations

#### Background Tasks with ui.timer
```python
import asyncio

@ui.page('/')
async def main():
    status = ui.label('Idle')
    
    async def long_task():
        status.text = 'Processing...'
        await asyncio.sleep(5)  # Simulate work
        status.text = 'Complete'
    
    # Run periodically
    ui.timer(10.0, long_task)
    
    # One-time background task
    ui.button('Start', on_click=long_task)
```

#### Proper Context for Background Operations
```python
from nicegui import ui, context

async def background_worker():
    """Background task needs explicit context"""
    with context.client:  # Attach to specific client
        ui.notify('Task complete')

@ui.page('/')
def main():
    ui.button('Start', on_click=lambda: asyncio.create_task(background_worker()))
```

### Component Organization

#### Reusable Components with Context Managers
```python
from contextlib import contextmanager

@contextmanager
def card_section(title: str):
    """Reusable card component"""
    with ui.card().classes('w-full'):
        ui.label(title).classes('text-h6')
        ui.separator()
        yield  # Content goes here

# Usage
with card_section('User Profile'):
    ui.label('Name: John Doe')
    ui.label('Email: john@example.com')
```

#### Class-Based Components
```python
class DataTable:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows
        self.selected = []
        self._build()
    
    def _build(self):
        with ui.card():
            self.table = ui.table(
                columns=self.columns,
                rows=self.rows,
                selection='multiple'
            )
            self.table.on('selection', self._on_select)
    
    def _on_select(self, e):
        self.selected = e.args['selected']
    
    def add_row(self, row):
        self.rows.append(row)
        self.table.update()
```

### Binding Patterns

#### Two-Way Data Binding
```python
class UserForm:
    def __init__(self):
        self.data = {'name': '', 'email': '', 'age': 0}
        
    def render(self):
        ui.input('Name').bind_value(self.data, 'name')
        ui.input('Email').bind_value(self.data, 'email')
        ui.number('Age').bind_value(self.data, 'age')
        ui.button('Submit', on_click=self.submit)
    
    def submit(self):
        print(f"Submitted: {self.data}")
```

#### Computed Properties
```python
from nicegui import ui

@ui.page('/')
def main():
    state = {'first': '', 'last': ''}
    
    ui.input('First Name').bind_value(state, 'first')
    ui.input('Last Name').bind_value(state, 'last')
    
    # Computed full name
    ui.label().bind_text_from(
        state, 'first',
        backward=lambda v: f"{state['first']} {state['last']}"
    )
```

### Error Handling

#### Graceful Degradation
```python
@ui.page('/')
async def main():
    try:
        data = await fetch_data()
        ui.table(columns=COLUMNS, rows=data)
    except ConnectionError:
        ui.label('Unable to connect to server').classes('text-red')
        ui.button('Retry', on_click=lambda: ui.open('/'))
    except Exception as e:
        ui.notify(f'Error: {e}', type='negative')
        logging.exception('Unexpected error in main page')
```

#### Context-Aware Error Handling
```python
from nicegui import app

@app.exception_handler(ValueError)
def handle_value_error(request, exception):
    ui.notify(f'Invalid input: {exception}', type='warning')
    return {'error': str(exception)}
```

## Anti-Patterns to Avoid

### State Management Mistakes

#### ❌ Refreshable Inside Page Function
```python
@ui.page('/')
def main():
    @ui.refreshable  # WRONG: Creates new refreshable per client
    def display():
        ui.label(shared_data)
    display()
```

**Problem**: Each client gets a separate refreshable instance. Calling `refresh()` from one client won't update others.

**Solution**: Move refreshable outside page function (see Essential Patterns above).

#### ❌ Passing State to refresh()
```python
@ui.refreshable
def display(state):
    ui.label(state['value'])

# WRONG: Passing state to refresh
ui.button('Update', on_click=lambda: display.refresh(new_state))
```

**Problem**: All clients see the same new state, losing per-client isolation.

**Solution**: Keep state reference in closure, only call `refresh()` without arguments.

#### ❌ Modifying Bound Objects Incorrectly
```python
data = {'items': [1, 2, 3]}
ui.label().bind_text_from(data, 'items')

# WRONG: Modifying list in-place doesn't trigger update
data['items'].append(4)

# CORRECT: Reassign to trigger binding
data['items'] = data['items'] + [4]
```

### Async/Await Issues

#### ❌ Blocking Operations in Event Handlers
```python
def slow_handler():
    time.sleep(5)  # WRONG: Blocks entire server
    ui.notify('Done')

ui.button('Process', on_click=slow_handler)
```

**Solution**: Use `async def` with `await asyncio.sleep()` or run in thread pool.

#### ❌ Missing Context in Background Tasks
```python
async def background_task():
    await asyncio.sleep(10)
    ui.notify('Done')  # WRONG: No client context

ui.button('Start', on_click=lambda: asyncio.create_task(background_task()))
```

**Solution**: Capture and use `context.client` (see Essential Patterns).

#### ❌ Forgetting await
```python
async def fetch_data():
    return await api.get('/data')

@ui.page('/')
async def main():
    data = fetch_data()  # WRONG: Returns coroutine, not data
    ui.label(data)  # Shows <coroutine object>
```

**Solution**: Always `await` async functions.

### Memory Leaks

#### ❌ Accumulating Timers
```python
@ui.page('/')
def main():
    def start_timer():
        ui.timer(1.0, lambda: print('tick'))  # WRONG: Creates new timer each call
    
    ui.button('Start', on_click=start_timer)
```

**Solution**: Store timer reference and cancel before creating new one.

```python
timer = None

def start_timer():
    global timer
    if timer:
        timer.cancel()
    timer = ui.timer(1.0, lambda: print('tick'))
```

#### ❌ Unbounded Data Growth
```python
messages = []  # Global list

@ui.page('/chat')
def chat():
    @ui.refreshable
    def display():
        for msg in messages:  # WRONG: List grows forever
            ui.label(msg)
```

**Solution**: Implement pagination or limit list size.

```python
MAX_MESSAGES = 100

def add_message(msg):
    messages.append(msg)
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)
    display.refresh()
```

#### ❌ Not Cleaning Up Resources
```python
@ui.page('/')
def main():
    connection = database.connect()  # WRONG: Never closed
    data = connection.query('SELECT * FROM users')
    ui.table(columns=COLUMNS, rows=data)
```

**Solution**: Use context managers or cleanup callbacks.

```python
@ui.page('/')
async def main():
    async with database.connect() as conn:
        data = await conn.query('SELECT * FROM users')
        ui.table(columns=COLUMNS, rows=data)
```

### UI Construction Errors

#### ❌ Creating Elements Outside Context
```python
label = ui.label('Hello')  # WRONG: No parent context

@ui.page('/')
def main():
    # label won't appear
    pass
```

**Solution**: Create elements inside page functions or with explicit parent.

#### ❌ Modifying Elements After Page Load
```python
@ui.page('/')
def main():
    label = ui.label('Initial')
    
    def update():
        label.text = 'Updated'  # CORRECT
        label.delete()  # WRONG: Leaves orphaned element
        ui.label('New')  # WRONG: No parent context
    
    ui.button('Update', on_click=update)
```

**Solution**: Use `ui.refreshable` for dynamic content.

```python
@ui.page('/')
def main():
    state = {'text': 'Initial'}
    
    @ui.refreshable
    def content():
        ui.label(state['text'])
    
    content()
    
    def update():
        state['text'] = 'Updated'
        content.refresh()
    
    ui.button('Update', on_click=update)
```

#### ❌ Excessive Nesting
```python
with ui.card():
    with ui.column():
        with ui.row():
            with ui.card():  # WRONG: Too many levels
                with ui.column():
                    ui.label('Deep')
```

**Solution**: Extract components into functions.

### Performance Issues

#### ❌ Refreshing Too Frequently
```python
@ui.refreshable
def expensive_display():
    # Heavy computation
    result = process_large_dataset()
    ui.label(result)

# WRONG: Refreshes on every keystroke
ui.input('Search').on('input', expensive_display.refresh)
```

**Solution**: Debounce updates or use `on_change` instead of `on('input')`.

```python
from asyncio import sleep

async def debounced_refresh():
    await sleep(0.5)  # Wait for typing to stop
    expensive_display.refresh()

ui.input('Search').on('input', lambda: asyncio.create_task(debounced_refresh()))
```

#### ❌ Large Data in Tables
```python
# WRONG: Rendering 10,000 rows
ui.table(columns=COLUMNS, rows=huge_dataset)
```

**Solution**: Implement pagination or virtual scrolling.

```python
PAGE_SIZE = 50

@ui.page('/')
def main():
    state = {'page': 0}
    
    @ui.refreshable
    def table_view():
        start = state['page'] * PAGE_SIZE
        end = start + PAGE_SIZE
        ui.table(columns=COLUMNS, rows=huge_dataset[start:end])
    
    table_view()
    
    with ui.row():
        ui.button('Previous', on_click=lambda: (
            state.update({'page': max(0, state['page'] - 1)}),
            table_view.refresh()
        ))
        ui.button('Next', on_click=lambda: (
            state.update({'page': state['page'] + 1}),
            table_view.refresh()
        ))
```

## Implementation Guidelines

### Project Structure
```
project/
├── main.py              # Entry point, ui.run()
├── pages/               # Page modules
│   ├── __init__.py
│   ├── home.py
│   └── dashboard.py
├── components/          # Reusable components
│   ├── __init__.py
│   ├── cards.py
│   └── forms.py
├── services/            # Business logic
│   ├── __init__.py
│   └── data_service.py
└── static/              # Static assets
    ├── css/
    └── images/
```

### Initialization Pattern
```python
# main.py
from nicegui import app, ui
from pages import home, dashboard

# Configure app
app.add_static_files('/static', 'static')

# Register pages
home.register()
dashboard.register()

# Run
ui.run(
    title='My App',
    port=8080,
    reload=True,  # Development only
    show=False    # Don't auto-open browser
)
```

### Page Module Pattern
```python
# pages/home.py
from nicegui import ui

def register():
    @ui.page('/')
    async def home_page():
        ui.label('Welcome').classes('text-h3')
        # Page content
```

### Component Module Pattern
```python
# components/cards.py
from nicegui import ui
from contextlib import contextmanager

@contextmanager
def info_card(title: str, icon: str = 'info'):
    with ui.card().classes('w-64'):
        with ui.row().classes('items-center'):
            ui.icon(icon).classes('text-2xl')
            ui.label(title).classes('text-h6')
        ui.separator()
        yield
```

### Testing Strategy
```python
# test_components.py
from nicegui.testing import Screen

def test_button_click():
    with Screen() as screen:
        counter = {'value': 0}
        
        def increment():
            counter['value'] += 1
        
        ui.button('Click', on_click=increment)
        
        screen.find('Click').click()
        assert counter['value'] == 1
```

## Success Metrics

### Performance Targets
- **Initial page load**: < 2 seconds
- **Interaction response**: < 100ms
- **Memory growth**: < 10MB per hour per client
- **WebSocket reconnection**: < 1 second

### Code Quality Indicators
- **Component reusability**: > 50% of UI code in reusable components
- **Test coverage**: > 80% for business logic
- **Async operations**: 100% of I/O operations use async/await
- **Error handling**: All user-facing operations have try/except

### User Experience Metrics
- **Perceived responsiveness**: All actions provide immediate feedback
- **Error recovery**: Users can recover from all error states
- **State persistence**: User preferences survive page reloads
- **Multi-client sync**: Shared data updates within 1 second across clients

## Sources & References

Content was rephrased for compliance with licensing restrictions.

1. [NiceGUI Official Repository](https://github.com/zauberzeug/nicegui)
2. [Global data store, per-user UI state Discussion](https://github.com/zauberzeug/nicegui/discussions/1029)
3. [NiceGUI Architecture Documentation](https://github.com/zauberzeug/nicegui)
4. [Memory leak issues](https://github.com/zauberzeug/nicegui/issues/1089)
5. [Refreshable documentation discussion](https://github.com/zauberzeug/nicegui/discussions/4321)
6. [Background task patterns](https://github.com/zauberzeug/nicegui/discussions/2893)
7. [NiceGUI Tutorial](https://wiki.bitplan.com/index.php/Nicegui_widgets/Tutorial)
8. [Python NiceGUI Guide](https://www.datacamp.com/tutorial/nicegui)

## Version History

- v1.0 (2026-01-15): Initial version based on research of NiceGUI documentation, GitHub discussions, and community patterns
