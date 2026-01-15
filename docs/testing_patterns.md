---
title:        Testing Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Testing Patterns

## Core Principles

1. **Test Behavior, Not Implementation** - Tests should verify what code does, not how it does it. Implementation details change; behavior contracts remain stable.

2. **Arrange-Act-Assert (AAA)** - Structure every test with clear setup, execution, and verification phases. One logical assertion per test.

3. **Fast, Isolated, Repeatable** - Tests must run quickly (<100ms unit tests), have no shared state, and produce identical results regardless of execution order or environment.

4. **Test at the Right Level** - Unit tests for logic, integration tests for boundaries, E2E tests for critical paths. Follow the testing pyramid (many unit, fewer integration, minimal E2E).

5. **Tests as Documentation** - Test names and structure should clearly communicate expected behavior. A failing test should immediately reveal what broke.

## Essential Patterns

### Given-When-Then (BDD Style)
```python
def test_user_login_with_valid_credentials_returns_token():
    # Given: a registered user
    user = create_user(email="test@example.com", password="secure123")
    
    # When: they login with correct credentials
    result = auth_service.login(email="test@example.com", password="secure123")
    
    # Then: they receive a valid token
    assert result.is_ok()
    assert result.value.token is not None
```

### Test Fixtures with Factory Pattern
```python
@dataclass
class UserFactory:
    """Deterministic test data generation."""
    
    @staticmethod
    def create(
        email: str = "user@test.com",
        role: Role = Role.USER,
        active: bool = True,
    ) -> User:
        return User(id=uuid4(), email=email, role=role, active=active)
```

### Parameterized Tests
```python
@pytest.mark.parametrize("input_val,expected", [
    ("", False),
    ("invalid", False),
    ("192.168.1.1", True),
    ("10.0.0.255", True),
    ("256.1.1.1", False),
])
def test_ip_validation(input_val: str, expected: bool):
    assert validate_ip(input_val) == expected
```

### Test Doubles Hierarchy
```python
# Stub: Returns canned responses
stub_repo = Mock(spec=UserRepository)
stub_repo.find_by_id.return_value = User(id=1, name="Test")

# Spy: Records interactions for verification
spy_logger = Mock(spec=Logger)
service.process(data)
spy_logger.info.assert_called_once_with("Processing complete")

# Fake: Working implementation with shortcuts
class FakeEmailService(EmailService):
    sent_emails: list[Email] = []
    
    def send(self, email: Email) -> None:
        self.sent_emails.append(email)
```

### Dependency Injection for Testability
```python
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        payment: PaymentGateway,
        notifier: Notifier,
    ) -> None:
        self._repo = repo
        self._payment = payment
        self._notifier = notifier
```

### Context Managers for Setup/Teardown
```python
@contextmanager
def database_transaction():
    conn = get_test_connection()
    try:
        yield conn
        conn.rollback()  # Always rollback test data
    finally:
        conn.close()
```

### Snapshot Testing for Complex Outputs
```python
def test_report_generation(snapshot):
    report = generate_quarterly_report(Q1_2026_DATA)
    assert report == snapshot  # Auto-generates on first run
```

### Contract Testing for APIs
```python
def test_api_contract_user_response():
    response = client.get("/api/users/1")
    
    # Verify structure, not specific values
    assert "id" in response.json()
    assert "email" in response.json()
    assert isinstance(response.json()["created_at"], str)
```

## Anti-Patterns to Avoid

### 1. **Test Interdependence**
```python
# BAD: Tests depend on execution order
class TestUserFlow:
    user_id = None
    
    def test_1_create_user(self):
        TestUserFlow.user_id = create_user().id  # Shared state!
    
    def test_2_update_user(self):
        update_user(TestUserFlow.user_id)  # Fails if test_1 didn't run
```

### 2. **Testing Implementation Details**
```python
# BAD: Breaks when refactoring internals
def test_user_service():
    service = UserService()
    service.create_user("test@example.com")
    assert service._cache["test@example.com"] is not None  # Private attribute!
    assert service._validate_email.call_count == 1  # Internal method!
```

### 3. **Excessive Mocking**
```python
# BAD: Test proves nothing about real behavior
def test_process_order():
    mock_repo = Mock()
    mock_payment = Mock()
    mock_inventory = Mock()
    mock_shipping = Mock()
    mock_notification = Mock()
    # ... 50 lines of mock setup
    # What are we even testing?
```

### 4. **Non-Deterministic Tests (Flaky Tests)**
```python
# BAD: Random failures
def test_async_operation():
    start_background_job()
    time.sleep(2)  # Hope it finishes!
    assert job_completed()  # Sometimes fails

# BAD: Time-dependent
def test_token_expiry():
    token = create_token()
    assert token.expires_at > datetime.now()  # Race condition
```

### 5. **Giant Test Methods**
```python
# BAD: Testing multiple behaviors
def test_user_registration():
    # 200 lines testing validation, persistence, 
    # email sending, audit logging, rate limiting...
```

### 6. **Assertion-Free Tests**
```python
# BAD: No verification
def test_process_data():
    data = load_test_data()
    result = process(data)  # No assert! Just checking it doesn't crash
```

### 7. **Hard-Coded Test Data Paths**
```python
# BAD: Breaks on different machines
def test_file_processing():
    result = process("/home/developer/test_data/file.csv")
```

### 8. **Ignoring Edge Cases**
```python
# BAD: Only happy path
def test_divide():
    assert divide(10, 2) == 5
    # Missing: divide(10, 0), divide(0, 5), divide(-10, 2)
```

### 9. **Copy-Paste Test Code**
```python
# BAD: Duplicated setup across 50 tests
def test_feature_1():
    user = User(id=1, name="Test", email="test@example.com", role=Role.ADMIN)
    # ... same 10 lines in every test
```

### 10. **Testing Framework Code**
```python
# BAD: Testing that pytest/mock works
def test_mock_returns_value():
    mock = Mock(return_value=42)
    assert mock() == 42  # Congratulations, you tested unittest.mock
```

## Implementation Guidelines

### Step 1: Test File Organization
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_validators.py
│   └── test_services.py
├── integration/             # Database, external services
│   ├── test_repositories.py
│   └── test_api_clients.py
├── e2e/                     # Full system tests
│   └── test_user_flows.py
├── conftest.py              # Shared fixtures
└── factories.py             # Test data factories
```

### Step 2: Naming Conventions
```python
# Pattern: test_<unit>_<scenario>_<expected_result>
def test_validate_email_with_invalid_format_returns_error():
def test_order_service_when_inventory_empty_raises_out_of_stock():
def test_user_repository_find_by_id_with_nonexistent_id_returns_none():
```

### Step 3: Fixture Strategy
```python
# conftest.py
@pytest.fixture
def db_session():
    """Provides isolated database session per test."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def authenticated_client(db_session):
    """Provides API client with authenticated user."""
    user = UserFactory.create()
    db_session.add(user)
    return TestClient(app, headers={"Authorization": f"Bearer {user.token}"})
```

### Step 4: Async Testing
```python
@pytest.mark.asyncio
async def test_async_fetch():
    async with aiohttp.ClientSession() as session:
        result = await fetch_data(session, "https://api.example.com")
    assert result.status == 200
```

### Step 5: Exception Testing
```python
def test_invalid_input_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        validate_user_input({"email": "not-an-email"})
    
    assert "email" in str(exc_info.value)
    assert exc_info.value.field == "email"
```

### Step 6: Coverage Configuration
```toml
# pyproject.toml
[tool.coverage.run]
branch = true
source = ["src"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 80
```

### Step 7: CI Integration
```yaml
# Run tests in parallel, fail fast
pytest tests/ -n auto --maxfail=3 -q

# Separate slow tests
pytest tests/unit -m "not slow"
pytest tests/integration -m "integration" --timeout=30
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Coverage** | ≥80% line, ≥70% branch | `pytest --cov --cov-branch` |
| **Test Execution Time** | Unit: <10s, Integration: <60s | CI pipeline metrics |
| **Flaky Test Rate** | <1% | Track failures without code changes |
| **Test-to-Code Ratio** | 1:1 to 2:1 | Lines of test / lines of production |
| **Mutation Score** | ≥70% | `mutmut run` |
| **Mean Time to Debug** | <15 min from failure | Track in incident reports |
| **Test Maintenance Burden** | <10% of dev time | Sprint retrospectives |

### Quality Indicators
- **Green builds on first push**: >90% of PRs
- **Tests catch bugs before production**: Track bugs found in prod vs tests
- **Refactoring confidence**: Can refactor without fear of breaking tests
- **New developer onboarding**: Tests serve as documentation

## Sources & References

- [pytest Documentation](https://docs.pytest.org/) — Official pytest framework documentation
- [Martin Fowler - Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html) — Testing strategy and test distribution
- [Google Testing Blog](https://testing.googleblog.com/) — Industry testing practices and patterns
- [Python Testing with pytest (Okken)](https://pragprog.com/titles/bopytest2/) — Comprehensive pytest patterns
- [xUnit Test Patterns (Meszaros)](http://xunitpatterns.com/) — Canonical test pattern reference
- [Working Effectively with Unit Tests (Fields)](https://leanpub.com/wewut) — Practical unit testing guidance

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
