---
title:        Nicegui Development Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15
status:       active
---

# Nicegui Development Best Practices

## Core Principles

### 1. Unified Architecture Over Decoupled Frontend/Backend
NiceGUI is built on FastAPI, enabling a single Python application to serve both API endpoints and UI. This eliminates the complexity of managing separate codebases, development environments, and API contracts between frontend and backend.

### 2. Server-Side State Management
Unlike JavaScript frameworks that manage state on the client, NiceGUI maintains UI state within the server's Python process. This simplifies application logic by eliminating complex state synchronization mechanisms between client and server.

### 3. Pythonic Abstraction of Web Technologies
NiceGUI functions as an abstraction layer generating HTML, CSS, and JavaScript from Python objects and methods. Developers define complex user interfaces without writing client-side code directly, leveraging Vue.js and Quasar under the hood.

### 4. Event-Driven Server-Side Execution
UI components are bound to Python callback functions that execute on the server. User interactions trigger these functions, creating a direct link between UI events and backend logic without HTTP round-trips.

### 5. Asynchronous-First Design
Built on ASGI (Asynchronous Server Gateway Interface), NiceGUI natively supports async operations for high-concurrency, I/O-bound tasks like network requests and database queries without blocking the server.

## Essential Practices

### Application Structure

#### Unified Application Pattern
```python
# app.py - Single entry point
from nicegui import ui, app
from fastapi import APIRouter

# Mount API routes onto NiceGUI's FastAPI instance
api_router = APIRouter()

@api_router.get("/api/data")
async def get_data():
    return {"data": "value"}

app.include_router(api_router)

# Define UI pages
@ui.page("/")
def main_page():
    ui.label("Main Page")

ui.run(port=8080)
```

#### Modular Component Organization
```
project/
├── src/
│   ├── backend/
│   │   ├── endpoints/      # API routes (APIRouter)
│   │   └── deps.py         # FastAPI dependency injection
│   ├── core/
│   │   ├── config.py       # Application configuration
│   │   └── security.py     # Authentication/authorization
│   ├── db/
│   │   ├── session.py      # Database session management
│   │   └── init_db.py      # Database initialization
│   ├── frontend/
│   │   ├── components/     # Reusable UI elements
│   │   ├── layouts/        # Page structure templates
│   │   ├── pages/          # UI views (@ui.page)
│   │   └── state.py        # UI state management
│   ├── models/             # SQLModel/Pydantic schemas
│   └── repositories/       # Business logic and data access
└── app.py                  # Application entry point
```

### State Management

#### Storage Hierarchy
```python
from nicegui import ui, app

# 1. General storage (shared across all users)
app.storage.general["global_config"] = {"theme": "dark"}

# 2. User storage (per authenticated user)
app.storage.user["preferences"] = {"language": "en"}

# 3. Browser storage (per browser session)
app.storage.browser["session_id"] = "abc123"

# 4. Tab storage (per browser tab)
app.storage.tab["current_view"] = "dashboard"
```

#### Reactive State with ui.refreshable
```python
from nicegui import ui

data = {"count": 0}

@ui.refreshable
def counter_display():
    ui.label(f"Count: {data['count']}")

@ui.page("/")
def main():
    counter_display()
    
    def increment():
        data["count"] += 1
        counter_display.refresh()
    
    ui.button("Increment", on_click=increment)

ui.run()
```

### Asynchronous Operations

#### Async Event Handlers
```python
from nicegui import ui
import asyncio

@ui.page("/")
def main():
    result_label = ui.label("Waiting...")
    
    async def fetch_data():
        result_label.text = "Loading..."
        await asyncio.sleep(2)  # Simulate async operation
        result_label.text = "Data loaded!"
    
    ui.button("Fetch", on_click=fetch_data)

ui.run()
```

#### Long-Running Operations
```python
from nicegui import ui
import asyncio

@ui.page("/")
def main():
    progress = ui.linear_progress(value=0)
    
    async def long_task():
        for i in range(100):
            await asyncio.sleep(0.1)
            progress.value = (i + 1) / 100
        ui.notify("Task complete!")
    
    ui.button("Start", on_click=long_task)

ui.run()
```

### Component Design

#### Reusable Components
```python
from nicegui import ui

def custom_card(title: str, content: str):
    """Reusable card component."""
    with ui.card():
        ui.label(title).classes("text-h6")
        ui.separator()
        ui.label(content)

@ui.page("/")
def main():
    custom_card("Title 1", "Content 1")
    custom_card("Title 2", "Content 2")

ui.run()
```

#### Separation of Concerns
```python
# components/header.py
from nicegui import ui

def header(user_name: str):
    with ui.header():
        ui.label(f"Welcome, {user_name}")
        ui.button("Logout", on_click=lambda: ui.navigate.to("/login"))

# pages/dashboard.py
from nicegui import ui
from components.header import header

@ui.page("/dashboard")
def dashboard():
    header("John Doe")
    ui.label("Dashboard content")
```

### Error Handling

#### Global Exception Handler
```python
from nicegui import ui, app

@app.exception_handler(Exception)
async def handle_exception(request, exc):
    ui.notify(f"Error: {str(exc)}", type="negative")
    return {"error": str(exc)}

@ui.page("/")
def main():
    def risky_operation():
        raise ValueError("Something went wrong")
    
    ui.button("Trigger Error", on_click=risky_operation)

ui.run()
```

#### User Feedback with Notifications
```python
from nicegui import ui

@ui.page("/")
def main():
    async def save_data():
        try:
            # Simulate save operation
            await asyncio.sleep(1)
            ui.notify("Data saved successfully!", type="positive")
        except Exception as e:
            ui.notify(f"Save failed: {str(e)}", type="negative")
    
    ui.button("Save", on_click=save_data)

ui.run()
```

### Routing and Navigation

#### Page Decorators
```python
from nicegui import ui

@ui.page("/")
def home():
    ui.label("Home Page")
    ui.button("Go to About", on_click=lambda: ui.navigate.to("/about"))

@ui.page("/about")
def about():
    ui.label("About Page")
    ui.button("Go Home", on_click=lambda: ui.navigate.to("/"))

ui.run()
```

#### Dynamic Routes
```python
from nicegui import ui

@ui.page("/user/{user_id}")
def user_profile(user_id: str):
    ui.label(f"User Profile: {user_id}")

ui.run()
```

### Testing

#### Unit Testing with Pytest
```python
# test_app.py
import pytest
from nicegui.testing import User

@pytest.fixture
def user():
    return User()

def test_button_click(user):
    from app import main
    
    user.open("/")
    user.find("Button").click()
    user.should_see("Clicked!")
```

#### Integration Testing
```python
# test_integration.py
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_api_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/data")
        assert response.status_code == 200
        assert response.json() == {"data": "value"}
```

## Anti-Patterns to Avoid

### 1. Blocking Operations in Event Handlers
**Bad:**
```python
import time

def slow_operation():
    time.sleep(5)  # Blocks entire server
    ui.notify("Done")

ui.button("Start", on_click=slow_operation)
```

**Good:**
```python
import asyncio

async def slow_operation():
    await asyncio.sleep(5)  # Non-blocking
    ui.notify("Done")

ui.button("Start", on_click=slow_operation)
```

### 2. Mixing UI and Business Logic
**Bad:**
```python
@ui.page("/")
def main():
    def save_user():
        # Business logic mixed with UI
        user = {"name": name_input.value}
        db.save(user)
        ui.notify("Saved")
    
    name_input = ui.input("Name")
    ui.button("Save", on_click=save_user)
```

**Good:**
```python
# repositories/user_repo.py
def save_user(name: str):
    user = {"name": name}
    db.save(user)

# pages/user.py
@ui.page("/")
def main():
    def save_user_handler():
        save_user(name_input.value)
        ui.notify("Saved")
    
    name_input = ui.input("Name")
    ui.button("Save", on_click=save_user_handler)
```

### 3. Ignoring Memory Management
**Bad:**
```python
# Global state without cleanup
connections = []

@ui.page("/")
def main():
    connections.append({"user": "john"})  # Memory leak
```

**Good:**
```python
from nicegui import ui, app

@ui.page("/")
def main():
    # Use storage with automatic cleanup
    app.storage.tab["connection"] = {"user": "john"}
```

### 4. Overusing ui.refreshable
**Bad:**
```python
@ui.refreshable
def entire_page():
    # Refreshing entire page on every change
    ui.label("Header")
    ui.label(f"Count: {count}")
    ui.label("Footer")
```

**Good:**
```python
def page():
    ui.label("Header")
    
    @ui.refreshable
    def counter():
        ui.label(f"Count: {count}")
    
    counter()
    ui.label("Footer")
```

### 5. Not Handling WebSocket Disconnections
**Bad:**
```python
# No error handling for connection loss
async def update_loop():
    while True:
        await asyncio.sleep(1)
        label.text = get_data()  # Fails if connection lost
```

**Good:**
```python
async def update_loop():
    try:
        while True:
            await asyncio.sleep(1)
            label.text = get_data()
    except Exception as e:
        ui.notify(f"Connection lost: {e}", type="warning")
```

## Implementation Guidelines

### Step 1: Project Setup
```bash
# Create project structure
mkdir -p src/{backend,core,db,frontend,models,repositories}
touch src/__init__.py app.py

# Install dependencies
pip install nicegui sqlmodel pydantic-settings
```

### Step 2: Configuration Management
```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My App"
    debug: bool = False
    database_url: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 3: Database Setup
```python
# src/db/session.py
from sqlmodel import create_engine, Session
from src.core.config import settings

engine = create_engine(settings.database_url)

def get_session():
    with Session(engine) as session:
        yield session
```

### Step 4: Define Models
```python
# src/models/user.py
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
```

### Step 5: Create Repository Layer
```python
# src/repositories/user_repo.py
from sqlmodel import Session, select
from src.models.user import User

def get_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()

def create_user(session: Session, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
```

### Step 6: Build UI Components
```python
# src/frontend/pages/users.py
from nicegui import ui
from src.db.session import get_session
from src.repositories.user_repo import get_users, create_user

@ui.page("/users")
def users_page():
    session = next(get_session())
    
    @ui.refreshable
    def user_list():
        users = get_users(session)
        for user in users:
            ui.label(f"{user.name} - {user.email}")
    
    user_list()
    
    with ui.dialog() as dialog:
        with ui.card():
            name_input = ui.input("Name")
            email_input = ui.input("Email")
            
            def add_user():
                create_user(session, name_input.value, email_input.value)
                user_list.refresh()
                dialog.close()
            
            ui.button("Add", on_click=add_user)
    
    ui.button("New User", on_click=dialog.open)
```

### Step 7: Production Deployment
```python
# app.py
from nicegui import ui
from src.frontend.pages import users

if __name__ == "__main__":
    ui.run(
        host="0.0.0.0",
        port=8080,
        reload=False,  # Disable in production
        show=False,    # Don't open browser
        storage_secret="your-secret-key"
    )
```

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      - db
  
  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Step 8: Nginx Reverse Proxy
```nginx
# /etc/nginx/sites-available/nicegui-app
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 9: Systemd Service
```ini
# /etc/systemd/system/nicegui-app.service
[Unit]
Description=NiceGUI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/nicegui-app
Environment="PATH=/opt/nicegui-app/venv/bin"
ExecStart=/opt/nicegui-app/venv/bin/python app.py

[Install]
WantedBy=multi-user.target
```

## Success Metrics

### Performance Indicators
- **Page Load Time**: < 2 seconds for initial page load
- **Interaction Response**: < 100ms for UI updates
- **WebSocket Latency**: < 50ms for real-time updates
- **Memory Usage**: Stable over time (no leaks)
- **Concurrent Users**: Support target user load without degradation

### Code Quality Metrics
- **Test Coverage**: > 80% for business logic
- **Component Reusability**: > 60% of UI components reused
- **Separation of Concerns**: Clear boundaries between UI, business logic, and data access
- **Type Coverage**: 100% type hints for public APIs
- **Documentation**: All public functions and classes documented

### Maintainability Indicators
- **Time to Add Feature**: Consistent across project lifecycle
- **Bug Fix Time**: Decreasing trend over time
- **Onboarding Time**: New developers productive within 1 week
- **Deployment Frequency**: Multiple times per week
- **Mean Time to Recovery**: < 1 hour for production issues

## Sources & References

1. [Guide to Building Integrated Web Applications with FastAPI and NiceGUI](https://jaehyeon.me/blog/2025-11-19-fastapi-nicegui-template/)
2. [Deployment of NiceGUI application](https://community.hetzner.com/tutorials/deploy-nicegui)
3. [NiceGUI Official Documentation](https://nicegui.io/documentation)
4. [NiceGUI GitHub Repository](https://github.com/zauberzeug/nicegui)
5. [FastAPI Production Deployment Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)
6. [Uvicorn Deployment Guide](https://www.uvicorn.org/deployment/)
7. [Python Unit Testing Best Practices](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/)
8. [Secrets of a Scalable Component Architecture](https://feature-sliced.design/blog/component-architecture-guide)

## Version History

- v1.0 (2026-01-15): Initial version based on 2025-2026 NiceGUI development research
