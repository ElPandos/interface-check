---
title:        Security Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Security Patterns

## Core Principles

1. **Defense in Depth**: Layer multiple security controls; never rely on a single mechanism. If one layer fails, others contain the breach.

2. **Least Privilege**: Grant minimum permissions required for a task. Revoke access immediately when no longer needed.

3. **Fail Secure**: When errors occur, default to denying access rather than granting it. Errors should not bypass security controls.

4. **Zero Trust**: Never trust, always verify. Authenticate and authorize every request regardless of network location.

5. **Secure by Default**: Ship with secure configurations. Users should opt-in to less secure options, not opt-out of security.

## Essential Patterns

### Authentication & Authorization

#### Token-Based Authentication
```python
from datetime import UTC, datetime, timedelta
from typing import Any
import secrets
import hashlib

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token."""
    return secrets.token_urlsafe(length)

def hash_token(token: str) -> str:
    """Hash token for storage - never store plaintext."""
    return hashlib.sha256(token.encode()).hexdigest()

def constant_time_compare(a: str, b: str) -> bool:
    """Prevent timing attacks on token comparison."""
    return secrets.compare_digest(a, b)
```

#### Role-Based Access Control (RBAC)
```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

class Permission(Enum):
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    ADMIN = auto()

@dataclass(frozen=True)
class Role:
    name: str
    permissions: frozenset[Permission]

class Authorizable(Protocol):
    def has_permission(self, permission: Permission) -> bool: ...

def require_permission(permission: Permission):
    """Decorator for permission-based access control."""
    def decorator(func):
        def wrapper(user: Authorizable, *args, **kwargs):
            if not user.has_permission(permission):
                raise PermissionError(f"Missing permission: {permission.name}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator
```

### Input Validation & Sanitization

#### Allowlist Validation
```python
from typing import TypeVar, Callable
from dataclasses import dataclass
import re

T = TypeVar("T")

@dataclass(frozen=True)
class ValidationResult[T]:
    value: T | None
    error: str | None
    
    @property
    def is_valid(self) -> bool:
        return self.error is None

def validate_allowlist(value: str, allowed: frozenset[str]) -> ValidationResult[str]:
    """Validate against explicit allowlist - prefer over blocklist."""
    if value in allowed:
        return ValidationResult(value, None)
    return ValidationResult(None, f"Value not in allowed set")

def validate_pattern(value: str, pattern: re.Pattern[str]) -> ValidationResult[str]:
    """Validate against regex pattern."""
    if pattern.fullmatch(value):
        return ValidationResult(value, None)
    return ValidationResult(None, "Value does not match required pattern")

# Example: strict hostname validation
HOSTNAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
```

#### Parameterized Queries (SQL Injection Prevention)
```python
# CORRECT: Parameterized query
def get_user_secure(conn, user_id: int) -> dict | None:
    cursor = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    return cursor.fetchone()

# WRONG: String interpolation - SQL injection vulnerable
def get_user_insecure(conn, user_id: str) -> dict | None:
    # NEVER DO THIS
    cursor = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
```

### Secret Management

#### Environment-Based Secrets
```python
import os
from dataclasses import dataclass
from typing import NoReturn

@dataclass(frozen=True)
class SecretConfig:
    """Load secrets from environment - never hardcode."""
    db_password: str
    api_key: str
    jwt_secret: str
    
    @classmethod
    def from_env(cls) -> "SecretConfig":
        def require_env(key: str) -> str:
            value = os.environ.get(key)
            if not value:
                raise EnvironmentError(f"Required secret {key} not set")
            return value
        
        return cls(
            db_password=require_env("DB_PASSWORD"),
            api_key=require_env("API_KEY"),
            jwt_secret=require_env("JWT_SECRET"),
        )
```

#### Secure Password Handling
```python
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash password with salt using modern algorithm."""
    salt = secrets.token_hex(32)
    # Use scrypt for password hashing (memory-hard)
    derived = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=2**14,  # CPU/memory cost
        r=8,      # Block size
        p=1,      # Parallelization
        dklen=64
    )
    return f"{salt}${derived.hex()}"

def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    salt, hash_hex = stored.split("$")
    derived = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=2**14, r=8, p=1, dklen=64
    )
    return secrets.compare_digest(derived.hex(), hash_hex)
```

### Secure Communication

#### TLS/SSL Configuration
```python
import ssl
from typing import Final

def create_secure_ssl_context() -> ssl.SSLContext:
    """Create hardened SSL context."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    ctx.load_default_certs()
    
    # Disable weak ciphers
    ctx.set_ciphers("ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20")
    
    return ctx

# SSH: Always verify host keys
SSH_STRICT_HOST_KEY: Final[str] = "StrictHostKeyChecking=yes"
```

### Logging & Audit

#### Secure Logging (No Secrets)
```python
import logging
import re
from typing import Any

class SecretFilter(logging.Filter):
    """Filter sensitive data from logs."""
    
    PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'password=***'),
        (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'api_key=***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'token=***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        for pattern, replacement in self.PATTERNS:
            msg = pattern.sub(replacement, msg)
        record.msg = msg
        return True
```

### Rate Limiting & DoS Prevention

```python
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock

@dataclass
class RateLimiter:
    """Token bucket rate limiter."""
    max_requests: int
    window_seconds: int
    _buckets: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    _lock: Lock = field(default_factory=Lock)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=self.window_seconds)
        
        with self._lock:
            # Remove expired entries
            self._buckets[key] = [
                t for t in self._buckets[key] if t > window_start
            ]
            
            if len(self._buckets[key]) >= self.max_requests:
                return False
            
            self._buckets[key].append(now)
            return True
```

## Anti-Patterns to Avoid

### 1. Hardcoded Secrets
```python
# WRONG - Never do this
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

# CORRECT - Use environment or secret manager
API_KEY = os.environ["API_KEY"]
```

### 2. Trusting User Input
```python
# WRONG - Command injection
def run_command(user_input: str):
    os.system(f"echo {user_input}")  # Shell injection!

# CORRECT - Use subprocess with list args
def run_command_safe(user_input: str):
    subprocess.run(["echo", user_input], shell=False, check=True)
```

### 3. Overly Permissive CORS
```python
# WRONG - Allows any origin
headers = {"Access-Control-Allow-Origin": "*"}

# CORRECT - Explicit allowlist
ALLOWED_ORIGINS = frozenset({"https://app.example.com", "https://admin.example.com"})
```

### 4. Logging Sensitive Data
```python
# WRONG - Exposes credentials in logs
logger.info(f"User login: {username}, password: {password}")

# CORRECT - Never log secrets
logger.info(f"User login attempt: {username}")
```

### 5. Disabled Certificate Verification
```python
# WRONG - Disables TLS verification (MITM vulnerable)
requests.get(url, verify=False)

# CORRECT - Always verify certificates
requests.get(url, verify=True)  # or verify="/path/to/ca-bundle.crt"
```

### 6. Weak Cryptography
```python
# WRONG - MD5/SHA1 for passwords
hashlib.md5(password.encode()).hexdigest()

# CORRECT - Use password-specific algorithms
hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
```

### 7. Security Through Obscurity
```python
# WRONG - Relying on hidden endpoints
@app.route("/admin-panel-x7k9m2")  # "Hidden" admin panel

# CORRECT - Proper authentication
@app.route("/admin")
@require_auth(role="admin")
```

### 8. Catching and Ignoring Exceptions
```python
# WRONG - Silently ignores auth failures
try:
    authenticate(user)
except Exception:
    pass  # User proceeds unauthenticated!

# CORRECT - Fail secure
try:
    authenticate(user)
except AuthenticationError:
    raise  # Deny access
```

## Implementation Guidelines

### Step 1: Threat Modeling
1. Identify assets (data, systems, credentials)
2. Identify threat actors (external attackers, insiders, automated bots)
3. Map attack surfaces (APIs, file uploads, user inputs)
4. Prioritize by impact × likelihood

### Step 2: Secure Development Lifecycle
1. **Design**: Security requirements in specs
2. **Code**: Static analysis (bandit, semgrep), dependency scanning
3. **Review**: Security-focused code review checklist
4. **Test**: SAST, DAST, penetration testing
5. **Deploy**: Hardened configurations, secrets management
6. **Monitor**: Logging, alerting, incident response

### Step 3: Dependency Management
```bash
# Scan for vulnerabilities
pip-audit
safety check

# Pin dependencies with hashes
pip-compile --generate-hashes requirements.in
```

### Step 4: Configuration Hardening
```python
# Production security settings
SECURE_DEFAULTS = {
    "DEBUG": False,
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Strict",
    "CSRF_ENABLED": True,
    "CONTENT_SECURITY_POLICY": "default-src 'self'",
}
```

### Step 5: Incident Response Preparation
1. Logging with correlation IDs
2. Alerting on anomalies
3. Documented runbooks
4. Regular security drills

## Success Metrics

### Quantitative Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Vulnerability scan findings (critical/high) | 0 | Weekly SAST/DAST |
| Mean time to patch critical CVEs | < 24 hours | Dependency tracking |
| Failed authentication rate | < 5% | Auth logs |
| Secrets in codebase | 0 | Pre-commit hooks |
| Test coverage on auth code | > 90% | Coverage reports |

### Qualitative Metrics
- Security review completion for all PRs touching auth/crypto
- Documented threat model updated quarterly
- Incident response drill completed quarterly
- All team members completed security training

### Monitoring Indicators
```python
# Key security events to monitor
SECURITY_EVENTS = [
    "authentication_failure",
    "authorization_denied", 
    "rate_limit_exceeded",
    "invalid_input_rejected",
    "certificate_error",
    "suspicious_pattern_detected",
]
```

## Sources & References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Industry standard web security risks
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — Practical security guidance
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/) — Most dangerous software weaknesses
- [Python Security Best Practices](https://python.org/dev/security/) — Python-specific guidance
- [NIST Cybersecurity Framework](https://nist.gov/cyberframework) — Risk management framework
- [Bandit Security Linter](https://bandit.readthedocs.io/) — Python static analysis tool

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version with core patterns, anti-patterns, and implementation guidelines
