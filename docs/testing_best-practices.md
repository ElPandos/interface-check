---
title:        Testing Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Testing Best Practices

## Core Principles

### 1. Tests Must Be Fast and Independent
Each test should execute in isolation without depending on other tests or shared mutable state. Fast tests enable rapid feedback loops—unit tests should run in milliseconds, not seconds.

### 2. Test One Thing Per Test
Each test should verify a single behavior or assertion. When a test fails, you should immediately know what broke. Using "and" in test descriptions signals the test should be split.

### 3. Follow the Testing Pyramid
Structure your test suite with many fast unit tests (~70%), fewer integration tests (~20%), and minimal end-to-end tests (~10%). This optimizes for speed, reliability, and maintenance cost.

### 4. Tests Are First-Class Code
Apply the same quality standards to test code as production code: clear naming, no duplication, proper abstractions. Refactor tests regularly.

### 5. Test Behavior, Not Implementation
Tests should verify what code does, not how it does it. Implementation-coupled tests break during refactoring even when behavior remains correct.

## Essential Practices

### Test Structure (Arrange-Act-Assert)
```python
def test_user_can_be_created_with_valid_email():
    # Arrange: Set up preconditions
    email = "user@example.com"
    
    # Act: Execute the behavior under test
    user = User.create(email=email)
    
    # Assert: Verify the expected outcome
    assert user.email == email
    assert user.is_active is True
```

### Naming Conventions
Use descriptive names that document behavior:
- `test_<unit>_<scenario>_<expected_result>`
- `test_user_with_invalid_email_raises_validation_error`
- `test_empty_cart_returns_zero_total`

### Fixtures and Setup
```python
import pytest

@pytest.fixture
def authenticated_client(db_session):
    """Provide an authenticated test client with database access."""
    user = UserFactory.create()
    client = TestClient(app)
    client.login(user)
    yield client
    # Cleanup happens automatically
```

### Mocking External Dependencies
Mock at boundaries, not internals:
```python
from unittest.mock import patch

def test_payment_service_handles_timeout():
    with patch("app.services.stripe_client") as mock_stripe:
        mock_stripe.charge.side_effect = TimeoutError()
        
        result = payment_service.process_payment(amount=100)
        
        assert result.status == "failed"
        assert result.error_code == "TIMEOUT"
```

### Property-Based Testing with Hypothesis
Test invariants across generated inputs:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sorting_preserves_length(items):
    sorted_items = sorted(items)
    assert len(sorted_items) == len(items)

@given(st.lists(st.integers()))
def test_sorting_is_idempotent(items):
    once = sorted(items)
    twice = sorted(once)
    assert once == twice
```

### Integration Testing
Test real interactions with controlled dependencies:
```python
@pytest.fixture(scope="session")
def postgres_container():
    """Spin up PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres.get_connection_url()

def test_user_repository_persists_data(postgres_container):
    repo = UserRepository(postgres_container)
    user = User(email="test@example.com")
    
    repo.save(user)
    retrieved = repo.get_by_email("test@example.com")
    
    assert retrieved.id == user.id
```

### Test Coverage Strategy
- Aim for 80%+ line coverage as a baseline
- Use mutation testing to validate test effectiveness
- Focus coverage on critical business logic
- Don't chase 100%—diminishing returns apply

```bash
# Run with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Mutation testing with mutmut
mutmut run --paths-to-mutate=src/
```

## Anti-Patterns to Avoid

### 1. Test Interdependence
**Bad**: Tests that depend on execution order or shared state
```python
# WRONG: Test B depends on Test A's side effects
class TestUser:
    user = None
    
    def test_a_create_user(self):
        TestUser.user = User.create("test@example.com")
    
    def test_b_user_has_email(self):
        assert TestUser.user.email == "test@example.com"  # Fails if A doesn't run first
```

### 2. Testing Implementation Details
**Bad**: Tests that break when refactoring without behavior change
```python
# WRONG: Testing internal method calls
def test_user_creation():
    with patch.object(User, '_generate_id') as mock:
        User.create("test@example.com")
        mock.assert_called_once()  # Breaks if implementation changes
```

### 3. The Giant Test
**Bad**: Tests that verify multiple unrelated behaviors
```python
# WRONG: Too many assertions, unclear what's being tested
def test_user_system():
    user = User.create("test@example.com")
    assert user.email == "test@example.com"
    assert user.is_active
    user.deactivate()
    assert not user.is_active
    user.change_email("new@example.com")
    assert user.email == "new@example.com"
```

### 4. Flaky Tests
**Bad**: Tests that pass/fail non-deterministically
- Avoid time-dependent assertions
- Don't rely on network calls in unit tests
- Use deterministic test data, not random values without seeds

### 5. Slow Test Suites
**Bad**: Tests that take minutes to run
- Mock expensive operations in unit tests
- Use in-memory databases for fast integration tests
- Parallelize test execution with `pytest-xdist`

### 6. Copy-Paste Test Code
**Bad**: Duplicated setup/assertion logic across tests
```python
# WRONG: Repeated setup
def test_admin_can_delete_user():
    admin = User.create("admin@example.com", role="admin")
    target = User.create("target@example.com")
    # ... test logic

def test_admin_can_ban_user():
    admin = User.create("admin@example.com", role="admin")  # Duplicated!
    target = User.create("target@example.com")  # Duplicated!
    # ... test logic
```

### 7. Ignoring Test Failures
**Bad**: Skipping or ignoring failing tests without resolution
- Fix or delete broken tests immediately
- Use `@pytest.mark.skip(reason="...")` only temporarily with tickets

## Implementation Guidelines

### Step 1: Project Setup
```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### Step 2: Directory Structure
```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── models.py
│       └── services.py
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/
│   │   └── test_repositories.py
│   └── e2e/
│       └── test_api.py
└── pyproject.toml
```

### Step 3: Shared Fixtures in conftest.py
```python
# tests/conftest.py
import pytest
from myapp.database import Database

@pytest.fixture(scope="session")
def db():
    """Session-scoped database connection."""
    database = Database(":memory:")
    database.create_tables()
    yield database
    database.close()

@pytest.fixture
def clean_db(db):
    """Function-scoped clean database state."""
    yield db
    db.rollback()
```

### Step 4: CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: pip install -e ".[test]"
      
      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration -v -m integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### Step 5: TDD Workflow (Red-Green-Refactor)
1. **Red**: Write a failing test that defines expected behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve code quality while keeping tests green
4. Repeat

## Success Metrics

### Quantitative Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Line Coverage | ≥80% | `pytest --cov` |
| Branch Coverage | ≥70% | `pytest --cov --cov-branch` |
| Mutation Score | ≥60% | `mutmut run` |
| Test Execution Time | <5 min (full suite) | CI pipeline duration |
| Unit Test Time | <10s | `pytest tests/unit` |
| Flaky Test Rate | <1% | CI failure analysis |

### Qualitative Indicators
- **Confidence to Refactor**: Can you change code without fear?
- **Bug Escape Rate**: How many bugs reach production?
- **Test Maintenance Burden**: How often do tests break without behavior changes?
- **Documentation Value**: Do tests explain system behavior?

### Test Health Dashboard
Track over time:
- Tests added per feature
- Test-to-code ratio
- Time spent debugging vs. prevented bugs
- Coverage trends (should be stable or increasing)

## Sources & References

- [Python Testing Best Practices: A Complete Guide for 2025](https://orchestrator.dev/blog/2024-12-21-python-testing-best-practices) — Comprehensive pytest guide with modern practices, accessed 2026-01-14
- [Python Unit Testing Best Practices](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/) — Detailed unit testing patterns and naming conventions, accessed 2026-01-14
- [How To Practice Test-Driven Development In Python](https://pytest-with-eric.com/tdd/pytest-tdd/) — TDD workflow and red-green-refactor cycle, accessed 2026-01-14
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/en/latest/) — Property-based testing framework reference, accessed 2026-01-14
- [The Testing Pyramid: Strategic Software Testing](https://circleci.com/blog/testing-pyramid/) — Test pyramid ratios and CI/CD integration, accessed 2026-01-14
- [AWS Testing Stages in CI/CD](https://docs.aws.amazon.com/whitepapers/latest/practicing-continuous-integration-continuous-delivery/testing-stages-in-continuous-integration-and-continuous-delivery.html) — Enterprise testing pipeline guidance, accessed 2026-01-14
- [Software Testing Anti-Patterns](https://testrigor.com/blog/anti-patterns-in-software-testing/) — Common testing mistakes and remediation, accessed 2026-01-14
- [Code Coverage vs Mutation Testing](https://journal.optivem.com/p/code-coverage-vs-mutation-testing-code-example) — Coverage metrics comparison and mutation testing value, accessed 2026-01-14
- [Modern Test Pyramid Guide 2025](https://fullscale.io/blog/modern-test-pyramid-guide/) — Adapted pyramid for microservices and cloud-native apps, accessed 2026-01-14

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
