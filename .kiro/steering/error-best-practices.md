---
title:        Error Handling Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Error Handling Best Practices

## Purpose
Establish comprehensive error handling practices for building resilient applications that gracefully handle failures, provide meaningful user feedback, and maintain system stability.

## Core Principles

### 1. Separation of Concerns
- **Clean Architecture**: Separate error handling logic from business logic
- **Readability**: Make code more maintainable by isolating error scenarios
- **Systematic Approach**: Anticipate failures and design recovery mechanisms
- **Layered Handling**: Handle errors at appropriate system layers

### 2. Resilience Patterns
- **Fail Fast**: Detect and report errors as early as possible
- **Graceful Degradation**: Provide reduced functionality when components fail
- **Fault Isolation**: Prevent failures from cascading across system boundaries
- **Recovery Mechanisms**: Implement automatic and manual recovery strategies

### 3. User Experience Focus
- **Meaningful Messages**: Provide clear, actionable error information
- **Context Preservation**: Maintain user state during error recovery
- **Progress Feedback**: Show recovery attempts and system status
- **Security Awareness**: Never expose sensitive system details

## Error Handling Patterns

### 1. Retry Pattern with Exponential Backoff

```python
import time
import random
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Any:
    """Retry function with exponential backoff and jitter."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            time.sleep(delay)
```

**Best Practices**:
- Use 3-5 retry attempts maximum
- Implement exponential backoff: 1s, 2s, 4s, 8s, 16s
- Add random jitter to prevent thundering herd
- Don't retry authentication failures or client errors (4xx)
- Ensure operations are idempotent

### 2. Circuit Breaker Pattern

```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

**Configuration Guidelines**:
- Set failure threshold based on service criticality (3-10 failures)
- Use timeout periods of 30-300 seconds
- Implement fallback responses for open circuit state
- Monitor circuit breaker state changes

### 3. Graceful Degradation

```python
from typing import Optional, Any

class ServiceFallback:
    def __init__(self, primary_service, fallback_service=None):
        self.primary_service = primary_service
        self.fallback_service = fallback_service
    
    def execute(self, operation: str, *args, **kwargs) -> Any:
        try:
            return getattr(self.primary_service, operation)(*args, **kwargs)
        except Exception as e:
            if self.fallback_service:
                try:
                    return getattr(self.fallback_service, operation)(*args, **kwargs)
                except Exception:
                    pass
            
            # Return degraded response
            return self._get_fallback_response(operation, e)
    
    def _get_fallback_response(self, operation: str, error: Exception) -> Any:
        return {
            "status": "degraded",
            "message": "Service temporarily unavailable",
            "operation": operation,
            "fallback": True
        }
```

## Exception Management

### 1. Exception Hierarchy

```python
class ApplicationError(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}

class ValidationError(ApplicationError):
    """Raised when input validation fails."""
    pass

class BusinessLogicError(ApplicationError):
    """Raised when business rules are violated."""
    pass

class ExternalServiceError(ApplicationError):
    """Raised when external service calls fail."""
    pass

class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid."""
    pass
```

### 2. Error Context and Logging

```python
import logging
import traceback
from typing import Dict, Any

class ErrorHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle error with proper logging and user response."""
        error_id = self._generate_error_id()
        
        # Log detailed error for developers
        self.logger.error(
            f"Error {error_id}: {str(error)}",
            extra={
                "error_id": error_id,
                "error_type": type(error).__name__,
                "context": context or {},
                "stack_trace": traceback.format_exc()
            }
        )
        
        # Return user-friendly response
        return {
            "error": True,
            "error_id": error_id,
            "message": self._get_user_message(error),
            "recoverable": self._is_recoverable(error)
        }
    
    def _get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message."""
        if isinstance(error, ValidationError):
            return str(error)
        elif isinstance(error, BusinessLogicError):
            return str(error)
        else:
            return "An unexpected error occurred. Please try again later."
    
    def _is_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable."""
        return not isinstance(error, (ConfigurationError, SystemExit))
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]
```

### 3. Structured Error Responses

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ErrorResponse:
    """Structured error response format."""
    error: bool = True
    error_code: str = ""
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    request_id: Optional[str] = None
    recoverable: bool = True
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": self.error,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "recoverable": self.recoverable
        }
```

## Logging Best Practices

### 1. Structured Logging Configuration

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'error_id'):
            log_entry['error_id'] = record.error_id
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        if hasattr(record, 'stack_trace'):
            log_entry['stack_trace'] = record.stack_trace
            
        return json.dumps(log_entry)

# Configure structured logging
def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

### 2. Log Levels and Usage

- **ERROR**: Exceptions preventing operation completion
- **WARNING**: Recoverable issues requiring attention
- **INFO**: Important events (user requests, system state changes)
- **DEBUG**: Detailed debugging information for development

### 3. Security Considerations

```python
import re
from typing import Any, Dict

class SecureLogger:
    """Logger that sanitizes sensitive information."""
    
    SENSITIVE_PATTERNS = [
        r'password["\s]*[:=]["\s]*[^"\s]+',
        r'token["\s]*[:=]["\s]*[^"\s]+',
        r'api[_-]?key["\s]*[:=]["\s]*[^"\s]+',
        r'secret["\s]*[:=]["\s]*[^"\s]+',
    ]
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def sanitize_data(self, data: Any) -> Any:
        """Remove sensitive information from log data."""
        if isinstance(data, str):
            for pattern in self.SENSITIVE_PATTERNS:
                data = re.sub(pattern, '[REDACTED]', data, flags=re.IGNORECASE)
        elif isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        
        return data
    
    def error(self, message: str, **kwargs):
        """Log error with sanitized data."""
        sanitized_kwargs = self.sanitize_data(kwargs)
        self.logger.error(message, extra=sanitized_kwargs)
```

## Testing Error Handling

### 1. Error Injection Testing

```python
import pytest
from unittest.mock import Mock, patch

class TestErrorHandling:
    def test_retry_mechanism(self):
        """Test retry logic with temporary failures."""
        mock_service = Mock()
        mock_service.call.side_effect = [
            Exception("Temporary failure"),
            Exception("Another failure"),
            "Success"
        ]
        
        result = retry_with_backoff(mock_service.call, max_attempts=3)
        assert result == "Success"
        assert mock_service.call.call_count == 3
    
    def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after threshold failures."""
        circuit_breaker = CircuitBreaker(failure_threshold=2)
        failing_func = Mock(side_effect=Exception("Service down"))
        
        # First two calls should fail and increment counter
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        with pytest.raises(Exception):
            circuit_breaker.call(failing_func)
        
        # Third call should be blocked by open circuit
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            circuit_breaker.call(failing_func)
    
    def test_graceful_degradation(self):
        """Test fallback behavior when primary service fails."""
        primary = Mock()
        primary.get_data.side_effect = Exception("Service unavailable")
        
        fallback = Mock()
        fallback.get_data.return_value = {"status": "cached", "data": "fallback"}
        
        service = ServiceFallback(primary, fallback)
        result = service.execute("get_data")
        
        assert result["status"] == "cached"
```

### 2. Chaos Engineering Principles

- **Controlled Failures**: Introduce failures in non-production environments first
- **Gradual Rollout**: Start with small-scale tests and expand gradually
- **Monitoring**: Ensure comprehensive monitoring during chaos experiments
- **Recovery Validation**: Verify systems recover within acceptable timeframes

## Performance Considerations

### 1. Error Handling Overhead

```python
# Efficient error checking for hot paths
def fast_validation(value: str) -> bool:
    """Use return codes instead of exceptions for expected cases."""
    if not value:
        return False
    if len(value) > 1000:
        return False
    return True

# Reserve exceptions for truly exceptional cases
def process_data(data: str) -> str:
    if not fast_validation(data):
        raise ValidationError("Invalid data format")
    
    # Process data...
    return processed_data
```

### 2. Resource Cleanup

```python
from contextlib import contextmanager
import logging

@contextmanager
def managed_resource(resource_factory):
    """Context manager for automatic resource cleanup."""
    resource = None
    try:
        resource = resource_factory()
        yield resource
    except Exception as e:
        logging.error(f"Error using resource: {e}")
        raise
    finally:
        if resource and hasattr(resource, 'close'):
            try:
                resource.close()
            except Exception as e:
                logging.warning(f"Error closing resource: {e}")
```

## Implementation Guidelines

### 1. Error Handling Strategy
- **Define Error Categories**: Business, validation, system, external service errors
- **Establish Recovery Patterns**: Retry, circuit breaker, fallback mechanisms
- **Implement Monitoring**: Error rates, recovery times, user impact metrics
- **Create Runbooks**: Document error scenarios and response procedures

### 2. Team Practices
- **Error Handling Reviews**: Include error scenarios in code reviews
- **Testing Requirements**: Mandate error path testing for all features
- **Documentation**: Maintain error handling patterns and examples
- **Training**: Regular training on resilience patterns and debugging

### 3. Monitoring and Alerting
- **Error Rate Thresholds**: Alert on unusual error rate increases
- **Recovery Time Tracking**: Monitor time to recover from failures
- **User Impact Metrics**: Track error impact on user experience
- **Correlation Analysis**: Link errors to system changes and deployments

## Common Anti-Patterns to Avoid

### 1. Error Handling Mistakes
- **Swallowing Exceptions**: Catching exceptions without proper handling
- **Generic Error Messages**: Providing unhelpful error information
- **Exposing Internal Details**: Revealing system internals in error messages
- **Infinite Retries**: Not limiting retry attempts or implementing backoff
- **Resource Leaks**: Failing to clean up resources in error paths

### 2. Logging Issues
- **Excessive Logging**: Logging too much information in production
- **Insufficient Context**: Not providing enough context for debugging
- **Security Violations**: Logging sensitive information
- **Performance Impact**: Synchronous logging in critical paths

### 3. User Experience Problems
- **Technical Error Messages**: Showing stack traces to end users
- **No Recovery Options**: Not providing ways for users to recover
- **Lost Context**: Losing user state during error handling
- **Poor Error Timing**: Not handling errors at appropriate times

## Success Metrics

- **Mean Time to Recovery (MTTR)**: Average time to recover from failures
- **Error Rate Trends**: Tracking error rates over time
- **User Experience Impact**: Measuring user satisfaction during errors
- **System Availability**: Overall system uptime and reliability
- **Error Resolution Time**: Time from error detection to resolution

## Version History

- v1.0 (2026-01-12): Initial version based on comprehensive research of current error handling best practices
