---
title:        Pydantic Models Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 15:14:27
status:       active
---

# Pydantic Models Patterns

## Core Principles

1. **Use Pydantic at service boundaries only** - Validation should occur at API request/response boundaries, not within internal service logic. This prevents serialization/deserialization overhead throughout your application.

2. **Prefer composition over inheritance** - Build models through composition rather than deep inheritance hierarchies. Duplication is cheaper than excessive abstraction layers.

3. **Type hints everywhere** - Leverage Python type annotations for all fields. This enables both runtime validation and static type checking with tools like mypy.

4. **Explicit validation over implicit coercion** - Use strict mode when type safety is critical. Understand when to use before/after/wrap validators based on your validation needs.

5. **Performance awareness** - Pydantic adds overhead (~6.5x slower creation, ~2.5x more memory than dataclasses). Use it where validation matters, not everywhere.

## Essential Patterns

### Model Definition Patterns

#### Basic Model Structure
```python
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
```

#### Nested Models for Complex Data
```python
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    zip_code: Optional[str] = None

class User(BaseModel):
    id: int
    name: str
    addresses: List[Address]
```

**Best practices for nested models:**
- Validate data at each nesting level
- Use clear, consistent naming conventions
- Keep models simple - break down overly complex structures
- Each nested model should have its own validation rules

#### Field Constraints and Custom Types
```python
from pydantic import BaseModel, Field, conint, constr, EmailStr

class Product(BaseModel):
    name: constr(min_length=2, max_length=50)
    quantity: conint(gt=0, le=1000)
    price: float = Field(gt=0, description="Price must be positive")
    email: EmailStr
```

#### Immutable Models with ConfigDict
```python
from pydantic import BaseModel, ConfigDict

class ImmutableConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    api_key: str
    timeout: int = 30

# Attempting to modify raises ValidationError
config = ImmutableConfig(api_key="secret")
# config.api_key = "new"  # Raises ValidationError
```

### Validation Patterns

#### Field Validators - After Mode (Most Common)
```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    age: int
    
    @field_validator('age', mode='after')
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 0 or value > 150:
            raise ValueError('Age must be between 0 and 150')
        return value
```

#### Field Validators - Before Mode (Type Coercion)
```python
from typing import Any
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    numbers: list[int]
    
    @field_validator('numbers', mode='before')
    @classmethod
    def ensure_list(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return [value]
        return value
```

#### Reusable Validators with Annotated
```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel

def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value

EvenNumber = Annotated[int, AfterValidator(is_even)]

class Model1(BaseModel):
    my_number: EvenNumber

class Model2(BaseModel):
    other_number: EvenNumber
    list_of_evens: list[EvenNumber]
```

#### Model Validators for Cross-Field Validation
```python
from typing_extensions import Self
from pydantic import BaseModel, model_validator

class UserModel(BaseModel):
    password: str
    password_repeat: str
    
    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError('Passwords do not match')
        return self
```

#### Wrap Validators for Error Handling
```python
from typing import Any
from pydantic import BaseModel, Field, WrapValidator, ValidatorFunctionWrapHandler
from typing import Annotated

def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
    try:
        return handler(value)
    except ValidationError as err:
        if err.errors()[0]['type'] == 'string_too_long':
            return handler(value[:5])
        raise

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]
```

### Computed Fields Pattern
```python
from pydantic import BaseModel, computed_field

class Player(BaseModel):
    first_name: str
    last_name: str
    
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

player = Player(first_name="John", last_name="Doe")
print(player.full_name)  # "John Doe"
print(player.model_dump())  # Includes full_name in output
```

### Alias Patterns for API Compatibility
```python
from pydantic import BaseModel, Field, ConfigDict

class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: int = Field(alias="userId")
    first_name: str = Field(alias="firstName")
    
# Accepts both snake_case and camelCase
model = APIModel(userId=1, firstName="John")
model = APIModel(user_id=1, first_name="John")  # Also works
```

### Strict Mode for Type Safety
```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)
    
    count: int
    name: str

# StrictModel(count="123")  # Raises ValidationError
StrictModel(count=123, name="test")  # OK
```

### Validation Context Pattern
```python
from pydantic import BaseModel, ValidationInfo, field_validator

class Model(BaseModel):
    text: str
    
    @field_validator('text', mode='after')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v

data = {'text': 'This is an example document'}
Model.model_validate(data, context={'stopwords': ['this', 'is']})
```

### Settings Management Pattern
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    api_key: str = Field(validation_alias='API_KEY')
    database_url: str = Field(validation_alias='DATABASE_URL')
    debug: bool = False
    
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

settings = Settings()  # Loads from environment variables
```

## Anti-Patterns to Avoid

### 1. SerDes Debt - Using Pydantic Everywhere
**Problem:** Using Pydantic models throughout internal service logic causes excessive serialization/deserialization overhead.

```python
# ❌ BAD: Pydantic used internally
class InternalService:
    def process(self, data: PydanticModel) -> PydanticModel:
        # Converting to/from Pydantic repeatedly
        result = PydanticModel(**data.model_dump())
        return result

# ✅ GOOD: Pydantic only at boundaries
class InternalService:
    def process(self, data: dict) -> dict:
        # Work with plain dicts internally
        return result

class APIHandler:
    def handle_request(self, raw_data: dict) -> dict:
        # Validate at boundary
        validated = RequestModel.model_validate(raw_data)
        result = service.process(validated.model_dump())
        return ResponseModel(**result).model_dump()
```

**Performance impact:**
- Pydantic creation: ~6.5x slower than dataclasses
- Memory consumption: ~2.5x more than dataclasses
- JSON operations: ~1.5x slower

### 2. Deep Inheritance Hierarchies
**Problem:** Complex inheritance chains create abstraction layers that are hard to maintain.

```python
# ❌ BAD: Deep inheritance
class BaseEntity(BaseModel):
    id: int
    created_at: datetime

class NamedEntity(BaseEntity):
    name: str

class DescribedEntity(NamedEntity):
    description: str

class Product(DescribedEntity):
    price: float

# ✅ GOOD: Composition
class Timestamps(BaseModel):
    created_at: datetime
    updated_at: datetime

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    timestamps: Timestamps
```

### 3. Mutable Default Arguments
**Problem:** Using mutable defaults causes shared state between instances.

```python
# ❌ BAD: Mutable default
class Model(BaseModel):
    tags: list[str] = []  # Shared between instances!

# ✅ GOOD: Use default_factory
from pydantic import Field

class Model(BaseModel):
    tags: list[str] = Field(default_factory=list)
```

### 4. Not Validating Default Values
**Problem:** Default values bypass validation by default.

```python
# ❌ BAD: Invalid default not caught
class Model(BaseModel):
    age: int = -5  # Invalid but not validated

# ✅ GOOD: Enable default validation
class Model(BaseModel):
    model_config = ConfigDict(validate_default=True)
    
    age: int = Field(default=18, ge=0)
```

### 5. Ignoring Validation Errors
**Problem:** Catching ValidationError without proper handling.

```python
# ❌ BAD: Silent failure
try:
    model = Model(**data)
except ValidationError:
    pass  # Error lost

# ✅ GOOD: Proper error handling
try:
    model = Model(**data)
except ValidationError as e:
    logger.error(f"Validation failed: {e.errors()}")
    raise HTTPException(status_code=422, detail=e.errors())
```

### 6. Overusing Plain Validators
**Problem:** Plain validators skip Pydantic's type validation entirely.

```python
# ❌ BAD: Plain validator allows invalid types
class Model(BaseModel):
    number: int
    
    @field_validator('number', mode='plain')
    @classmethod
    def validate(cls, value: Any) -> Any:
        return value  # Accepts anything!

# ✅ GOOD: Use after validator
class Model(BaseModel):
    number: int
    
    @field_validator('number', mode='after')
    @classmethod
    def validate(cls, value: int) -> int:
        if value < 0:
            raise ValueError('Must be positive')
        return value
```

### 7. Not Using Type Hints Properly
**Problem:** Missing or incorrect type hints defeat Pydantic's purpose.

```python
# ❌ BAD: No type hints
class Model(BaseModel):
    data = None  # Type unknown

# ✅ GOOD: Explicit types
class Model(BaseModel):
    data: Optional[dict[str, Any]] = None
```

### 8. Circular Dependencies
**Problem:** Models referencing each other cause import issues.

```python
# ❌ BAD: Circular reference
class User(BaseModel):
    posts: list['Post']

class Post(BaseModel):
    author: User  # Circular!

# ✅ GOOD: Use forward references and model_rebuild
from __future__ import annotations

class User(BaseModel):
    posts: list[Post] = []

class Post(BaseModel):
    author: User

User.model_rebuild()  # Resolve forward references
```

## Implementation Guidelines

### Step 1: Define Your Data Boundaries
Identify where data enters and exits your system:
- API endpoints (request/response)
- Database queries (ORM models separate from Pydantic)
- External service calls
- Configuration files

### Step 2: Create Boundary Models
```python
# API layer - Pydantic for validation
class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

# Internal layer - Plain dataclasses or dicts
@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime
```

### Step 3: Implement Validation Strategy
Choose validator types based on needs:

| Validator Type | Use When | Example |
|----------------|----------|---------|
| After | Type-safe validation after Pydantic parsing | Range checks, business rules |
| Before | Need to coerce input types | Converting strings to lists |
| Wrap | Need error recovery or conditional logic | Truncating too-long strings |
| Model | Cross-field validation required | Password confirmation |

### Step 4: Configure Model Behavior
```python
class MyModel(BaseModel):
    model_config = ConfigDict(
        # Validation
        strict=False,              # Allow type coercion
        validate_default=True,     # Validate default values
        validate_assignment=True,  # Validate on field assignment
        
        # Serialization
        use_enum_values=True,      # Serialize enums as values
        populate_by_name=True,     # Accept both alias and field name
        
        # Immutability
        frozen=False,              # Allow mutation
        
        # Performance
        arbitrary_types_allowed=False,  # Strict type checking
    )
```

### Step 5: Handle Errors Gracefully
```python
from pydantic import ValidationError

def create_user(data: dict) -> UserResponse:
    try:
        request = CreateUserRequest.model_validate(data)
    except ValidationError as e:
        # Log structured errors
        logger.error("Validation failed", extra={
            "errors": e.errors(),
            "input": data
        })
        # Return user-friendly errors
        raise HTTPException(
            status_code=422,
            detail=[{
                "field": err["loc"][0],
                "message": err["msg"]
            } for err in e.errors()]
        )
    
    # Process with validated data
    user = service.create_user(request.model_dump())
    return UserResponse(**user)
```

### Step 6: Test Your Models
```python
import pytest
from pydantic import ValidationError

def test_user_validation():
    # Valid data
    user = User(id=1, name="John", email="john@example.com")
    assert user.name == "John"
    
    # Invalid data
    with pytest.raises(ValidationError) as exc_info:
        User(id="invalid", name="John", email="not-an-email")
    
    errors = exc_info.value.errors()
    assert len(errors) == 2
    assert errors[0]["type"] == "int_parsing"
    assert errors[1]["type"] == "value_error"
```

## Success Metrics

### Validation Coverage
- **Target:** 100% of external inputs validated
- **Measure:** Count validated endpoints vs total endpoints
- **Tool:** Code coverage for model instantiation

### Performance Benchmarks
- **Creation time:** Monitor model instantiation latency
- **Memory usage:** Track memory consumption in production
- **Serialization overhead:** Measure JSON encode/decode times

### Error Rate Reduction
- **Invalid data errors:** Should decrease after Pydantic adoption
- **Type errors:** Runtime type errors should be caught at boundaries
- **Data corruption:** Incidents from malformed data should drop

### Code Quality Indicators
- **Type coverage:** Percentage of code with type hints
- **Mypy compliance:** Zero type checking errors
- **Validator reuse:** Number of shared validators across models

### Developer Experience
- **Time to add validation:** Should decrease with reusable patterns
- **Bug discovery time:** Validation errors caught earlier in development
- **Documentation clarity:** Self-documenting models via type hints

## Sources & References

1. [Best Practices for Using Pydantic in Python - Developer Service Blog](https://developer-service.blog/best-practices-for-using-pydantic-in-python/)
2. [Pydantic Is All You Need for Poor Performance Spaghetti Code](https://leehanchung.github.io/blogs/2025/07/03/pydantic-is-all-you-need-for-performance-spaghetti/)
3. [Pydantic Validators - Official Documentation](https://docs.pydantic.dev/latest/concepts/validators/)
4. [Master High-Performance Data Modeling and Validation - Innovirtuoso](https://innovirtuoso.com/data-engineering/learn-pydantic-v2-master-high-performance-data-modeling-and-validation-for-apis-ml-and-cloud/)
5. [Building Reliable LLM Workflows with Pydantic - Ylang Labs](https://ylanglabs.com/blogs/building-reliable-llm-workflows-with-pydantic)
6. [A Practical Guide to using Pydantic - Medium](https://medium.com/@marcnealer/a-practical-guide-to-using-pydantic-8aafa7feebf6)
7. [Pydantic: A Guide With Practical Examples - DataCamp](https://www.datacamp.com/tutorial/pydantic)
8. [FastAPI Model Design: Pydantic vs SQLAlchemy - OpenIllumi](https://openillumi.com/en/en-fastapi-pydantic-sqlalchemy-roles/)
9. [Advanced Pydantic Features - TK1S](https://www.tk1s.com/python/advanced-pydantic-features-custom-validators-and-complex-data-structures.html)
10. [Pydantic Performance Documentation](https://docs.pydantic.dev/latest/concepts/performance/)

## Version History

- v1.0 (2026-01-15 15:14:27): Initial version based on comprehensive research of Pydantic v2 patterns and anti-patterns
