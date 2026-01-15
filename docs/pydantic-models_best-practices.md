---
title:        Pydantic Models Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15
status:       active
---

# Pydantic Models Best Practices

## Core Principles

1. **Strict Validation by Default**: Use strict mode to prevent silent type coercion and catch data quality issues early
2. **Performance-First Design**: Leverage Pydantic v2's Rust-powered core (4-50x faster than v1) through optimal patterns
3. **Type Safety**: Combine runtime validation with static type checking for maximum reliability
4. **Immutability When Appropriate**: Use frozen models for data integrity in value objects and configuration
5. **Explicit Over Implicit**: Clear field definitions, validators, and serialization rules prevent surprises

## Essential Practices

### Model Configuration

Use `ConfigDict` for model-wide settings:

```python
from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config = ConfigDict(
        strict=True,              # No type coercion
        frozen=True,              # Immutable after creation
        extra='forbid',           # Reject unexpected fields
        validate_assignment=True, # Validate on field updates
        str_strip_whitespace=True # Auto-strip strings
    )
    
    name: str
    age: int = Field(ge=0, le=150)
```

**Key Configuration Options**:
- `strict=True`: Disable type coercion (e.g., `"123"` won't become `123`)
- `frozen=True`: Make instances immutable and hashable
- `extra='forbid'`: Raise ValidationError on unexpected fields
- `validate_assignment=True`: Re-validate when fields are modified
- `validate_default=True`: Validate default values at model creation

### Field Definitions

Use `Field()` for constraints and metadata:

```python
from pydantic import BaseModel, Field
from typing import Annotated

class Product(BaseModel):
    # Constraints
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price in USD")
    quantity: int = Field(ge=0, default=0)
    
    # Aliases for serialization/validation
    product_id: str = Field(alias="id", serialization_alias="productId")
    
    # Annotated pattern (reusable)
    PositiveInt = Annotated[int, Field(gt=0)]
    stock: PositiveInt
```

**Field Parameters**:
- Numeric: `gt`, `ge`, `lt`, `le`, `multiple_of`
- String: `min_length`, `max_length`, `pattern` (regex)
- General: `default`, `default_factory`, `alias`, `description`
- Validation: `strict`, `frozen` (field-level override)

### Validators

Use `@field_validator` for custom validation logic:

```python
from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import Self

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str
    password_confirm: str
    
    # Field validator (after Pydantic's validation)
    @field_validator('email', mode='after')
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        if not value.endswith('@company.com'):
            raise ValueError('Must use company email')
        return value
    
    # Before validator (pre-processing)
    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower().strip()
    
    # Model validator (cross-field validation)
    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self
```

**Validator Modes**:
- `mode='after'`: Run after Pydantic validation (type-safe, recommended)
- `mode='before'`: Run before Pydantic validation (raw input, more flexible)
- `mode='wrap'`: Full control, can skip validation (avoid for performance)
- `mode='plain'`: Terminates validation immediately (rarely needed)

### Computed Fields

Use `@computed_field` for derived values:

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float
    
    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @computed_field
    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

rect = Rectangle(width=10, height=5)
print(rect.area)  # 50.0
print(rect.model_dump())  # Includes computed fields
```

### Strict Mode Usage

Enable strict mode to prevent silent coercion:

```python
from pydantic import BaseModel, Field, StrictInt, StrictStr
from typing import Annotated

# Model-level strict mode
class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)
    value: int

# Field-level strict mode
class MixedModel(BaseModel):
    strict_field: int = Field(strict=True)
    lax_field: int  # Allows coercion

# Using Strict types
class TypedModel(BaseModel):
    count: StrictInt      # No coercion
    name: StrictStr       # No coercion
    flexible: int         # Allows "123" -> 123
```

**When to Use Strict Mode**:
- API request validation (prevent client errors)
- Configuration files (catch typos early)
- Database models (ensure data integrity)
- Internal data structures (type safety)

### Performance Optimization

#### Use `model_validate_json()` for JSON

```python
import json
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# ❌ Slow: Parse JSON in Python, then validate
data = json.loads('{"name": "John", "age": 30}')
user = User.model_validate(data)

# ✅ Fast: Validate directly from JSON (Rust-powered)
user = User.model_validate_json('{"name": "John", "age": 30}')
```

#### Instantiate TypeAdapter Once

```python
from pydantic import TypeAdapter

# ❌ Bad: Creates new validator each call
def process_items(items: list[dict]):
    adapter = TypeAdapter(list[int])
    return adapter.validate_python(items)

# ✅ Good: Reuse validator
adapter = TypeAdapter(list[int])

def process_items(items: list[dict]):
    return adapter.validate_python(items)
```

#### Use Specific Types Over Generic

```python
from typing import Sequence, Mapping

# ❌ Slower: Checks multiple sequence types
class Model1(BaseModel):
    items: Sequence[int]
    data: Mapping[str, int]

# ✅ Faster: Direct type check
class Model2(BaseModel):
    items: list[int]
    data: dict[str, int]
```

#### Use Tagged Unions (Discriminated Unions)

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

# ❌ Slow: Tries each type until one works
class Cat(BaseModel):
    name: str
    meow: str

class Dog(BaseModel):
    name: str
    bark: str

class SlowPet(BaseModel):
    pet: Union[Cat, Dog]

# ✅ Fast: Uses discriminator field
class FastCat(BaseModel):
    type: Literal['cat'] = 'cat'
    name: str
    meow: str

class FastDog(BaseModel):
    type: Literal['dog'] = 'dog'
    name: str
    bark: str

class FastPet(BaseModel):
    pet: Union[FastCat, FastDog] = Field(discriminator='type')
```

#### Use TypedDict for Nested Structures

```python
from typing_extensions import TypedDict
from pydantic import BaseModel

# ❌ Slower: Nested model validation
class Address(BaseModel):
    street: str
    city: str

class SlowUser(BaseModel):
    name: str
    address: Address

# ✅ Faster: TypedDict (2.5x faster)
class AddressDict(TypedDict):
    street: str
    city: str

class FastUser(BaseModel):
    name: str
    address: AddressDict
```

### Serialization and Aliases

Control how models serialize:

```python
from pydantic import BaseModel, Field, ConfigDict

class APIResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  # Accept both alias and field name
        alias_generator=lambda x: ''.join(word.capitalize() for word in x.split('_'))
    )
    
    # Different aliases for validation vs serialization
    user_id: str = Field(
        validation_alias='userId',      # Accept this in input
        serialization_alias='id'        # Output as this
    )
    
    created_at: str  # Auto-converted to CreatedAt via alias_generator

# Serialization options
response = APIResponse(userId='123', created_at='2026-01-15')
print(response.model_dump())                    # Python dict
print(response.model_dump_json())               # JSON string
print(response.model_dump(by_alias=True))       # Use serialization aliases
print(response.model_dump(exclude={'user_id'})) # Exclude fields
```

### Settings Management

Use `pydantic-settings` for configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='APP_',
        case_sensitive=False
    )
    
    database_url: str
    api_key: str
    debug: bool = False
    max_connections: int = 10

# Loads from environment variables: APP_DATABASE_URL, APP_API_KEY, etc.
settings = Settings()
```

## Anti-Patterns to Avoid

### 1. Over-Using Wrap Validators

```python
# ❌ Bad: Wrap validators are slow
@field_validator('value', mode='wrap')
@classmethod
def validate_value(cls, value, handler):
    result = handler(value)
    return result * 2

# ✅ Good: Use after validators
@field_validator('value', mode='after')
@classmethod
def validate_value(cls, value: int) -> int:
    return value * 2
```

### 2. Subclassing Primitives for Extra Data

```python
# ❌ Bad: Breaks validation assumptions
class CompletedStr(str):
    def __init__(self, s: str):
        self.done = False

# ✅ Good: Use proper model
class CompletedModel(BaseModel):
    text: str
    done: bool = False
```

### 3. Not Validating Default Values

```python
# ❌ Bad: Invalid default not caught
class Model(BaseModel):
    age: int = Field(ge=0, default=-1)  # Invalid!

# ✅ Good: Validate defaults
class Model(BaseModel):
    model_config = ConfigDict(validate_default=True)
    age: int = Field(ge=0, default=0)
```

### 4. Using `Any` When Type is Known

```python
from typing import Any

# ❌ Bad: Skips validation
class Model(BaseModel):
    data: Any  # No validation!

# ✅ Good: Use proper type
class Model(BaseModel):
    data: dict[str, int]  # Validated
```

### 5. Ignoring Validation Errors

```python
# ❌ Bad: Silent failures
try:
    user = User(**data)
except Exception:
    pass  # Lost error information

# ✅ Good: Handle validation errors
from pydantic import ValidationError

try:
    user = User(**data)
except ValidationError as e:
    print(e.errors())  # Detailed error info
    # Log, return error response, etc.
```

### 6. Mutating Validated Data

```python
# ❌ Bad: Bypasses validation
user = User(name="John", age=30)
user.__dict__['age'] = -1  # Invalid but not caught

# ✅ Good: Use frozen or validate_assignment
class User(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    name: str
    age: int = Field(ge=0)

user = User(name="John", age=30)
user.age = -1  # Raises ValidationError
```

### 7. Not Using Discriminated Unions

```python
from typing import Union

# ❌ Bad: Slow union validation
class Response(BaseModel):
    data: Union[SuccessData, ErrorData]  # Tries both types

# ✅ Good: Use discriminator
class SuccessData(BaseModel):
    status: Literal['success'] = 'success'
    result: str

class ErrorData(BaseModel):
    status: Literal['error'] = 'error'
    message: str

class Response(BaseModel):
    data: Union[SuccessData, ErrorData] = Field(discriminator='status')
```

## Implementation Guidelines

### Step 1: Define Model Structure

```python
from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    """User model with validation."""
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra='forbid'
    )
    
    id: int = Field(gt=0)
    username: str = Field(min_length=3, max_length=50)
    email: str
    is_active: bool = True
```

### Step 2: Add Custom Validators

```python
from pydantic import field_validator
import re

class User(BaseModel):
    # ... (previous fields)
    
    @field_validator('email', mode='after')
    @classmethod
    def validate_email(cls, value: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValueError('Invalid email format')
        return value
    
    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower().strip()
```

### Step 3: Add Computed Fields

```python
from pydantic import computed_field

class User(BaseModel):
    # ... (previous fields)
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"@{self.username}"
```

### Step 4: Configure Serialization

```python
class User(BaseModel):
    model_config = ConfigDict(
        # ... (previous config)
        alias_generator=lambda x: ''.join(word.capitalize() for word in x.split('_'))
    )
    
    # ... (fields)
    
    def to_api_response(self) -> dict:
        return self.model_dump(
            by_alias=True,
            exclude={'id'},
            mode='json'
        )
```

### Step 5: Add Tests

```python
import pytest
from pydantic import ValidationError

def test_user_validation():
    # Valid user
    user = User(
        id=1,
        username="john_doe",
        email="john@example.com"
    )
    assert user.username == "john_doe"
    
    # Invalid email
    with pytest.raises(ValidationError) as exc:
        User(id=1, username="john", email="invalid")
    assert 'email' in str(exc.value)
    
    # Strict mode catches type coercion
    with pytest.raises(ValidationError):
        User(id="1", username="john", email="john@example.com")
```

## Success Metrics

### Validation Coverage
- **Target**: 100% of input data validated
- **Measure**: No unvalidated `Any` types in production models
- **Tool**: MyPy with strict mode, Pydantic's `model_json_schema()`

### Performance
- **Target**: <1ms validation time for typical models
- **Measure**: Benchmark with `timeit` for critical paths
- **Optimization**: Use `model_validate_json()`, TypedDict, discriminated unions

### Type Safety
- **Target**: Zero type-related runtime errors
- **Measure**: MyPy strict mode passes, no `type: ignore` comments
- **Tool**: MyPy, Pyright, or Pylance

### Error Quality
- **Target**: Clear, actionable validation errors
- **Measure**: Error messages include field name, expected type, received value
- **Tool**: Pydantic's built-in error formatting

### Code Maintainability
- **Target**: Models are self-documenting
- **Measure**: Field descriptions, type hints, validator docstrings
- **Tool**: Code review, documentation generation

## Sources & References

Content was rephrased for compliance with licensing restrictions.

1. [Pydantic V2 Plan](https://pydantic.dev/articles/pydantic-v2)
2. [Deep Dive into Pydantic V2 Core Changes](https://leapcell.io/blog/deep-dive-into-pydantic-v2-core-changes)
3. [Migrating to Pydantic V2](https://medium.com/codex/migrating-to-pydantic-v2-5a4b864621c3)
4. [A Practical Guide to using Pydantic](https://medium.com/@marcnealer/a-practical-guide-to-using-pydantic-8aafa7feebf6)
5. [Obtain a 5x speedup for free by upgrading to Pydantic v2](https://thedataquarry.com/blog/why-pydantic-v2-matters)
6. [Pydantic Configuration (ConfigDict)](https://the-pocket.github.io/PocketFlow-Tutorial-Codebase-Knowledge/Pydantic%20Core/03_configuration__configdict___configwrapper_.html)
7. [Pydantic Strict Mode Documentation](https://docs.pydantic.dev/latest/concepts/strict_mode/)
8. [Pydantic Validators Documentation](https://docs.pydantic.dev/latest/concepts/validators/)
9. [Pydantic Performance Tips](https://docs.pydantic.dev/latest/concepts/performance/)
10. [Advanced Pydantic Features: Custom Validators](https://www.tk1s.com/python/advanced-pydantic-features-custom-validators-and-complex-data-structures.html)
11. [Clean Validation with Pydantic v2](https://han8931.github.io/pydantic/)
12. [Pydantic Strict Validation: Forbid Extra Fields](https://openillumi.com/en/en-pydantic-forbid-extra-fields/)
13. [Pydantic Computed Fields Techniques](https://openillumi.com/en/en-pydantic-calculated-field-define-methods/)
14. [Best Practices for Using Pydantic in Python](https://dev.to/devasservice/best-practices-for-using-pydantic-in-python-2021)

## Version History

- v1.0 (2026-01-15): Initial version based on Pydantic v2 documentation and community best practices
