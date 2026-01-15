---
title:        Security Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Security Best Practices

## Core Principles

1. **Defense in Depth**: Layer multiple security controls; never rely on a single mechanism. Combine input validation, authentication, authorization, encryption, and monitoring.

2. **Least Privilege**: Grant minimum permissions required for functionality. Apply to users, services, API keys, and file system access. Revoke access immediately when no longer needed.

3. **Secure by Default**: Ship with secure configurations enabled. Require explicit opt-in for risky features. Fail closed rather than open on errors.

4. **Zero Trust**: Verify every request regardless of source. Authenticate and authorize at every boundary. Assume the network is compromised.

5. **Secrets as Ephemeral**: Treat credentials as short-lived. Rotate regularly, use dynamic credential generation where possible, and never hardcode secrets.

## Essential Practices

### Secrets Management

**Never hardcode credentials:**
```python
# WRONG - hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

# CORRECT - environment variables or secrets manager
import os
from pydantic import SecretStr

API_KEY = SecretStr(os.environ["API_KEY"])
DB_PASSWORD = SecretStr(os.environ["DB_PASSWORD"])
```

**Use Pydantic SecretStr for sensitive data:**
```python
from pydantic import BaseModel, SecretStr

class DatabaseConfig(BaseModel):
    host: str
    username: str
    password: SecretStr  # Won't appear in logs/repr

    def get_connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password.get_secret_value()}@{self.host}"
```

**Secrets management hierarchy:**
1. Hardware Security Modules (HSM) for critical keys
2. Cloud secrets managers (AWS Secrets Manager, HashiCorp Vault)
3. Environment variables (for containerized deployments)
4. Encrypted configuration files (last resort)

### Input Validation & Sanitization

**Validate all external input:**
```python
from pydantic import BaseModel, Field, field_validator
import re

class UserInput(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    
    @field_validator("username")
    @classmethod
    def no_sql_injection(cls, v: str) -> str:
        dangerous = ["'", '"', ";", "--", "/*", "*/", "xp_"]
        if any(d in v.lower() for d in dangerous):
            raise ValueError("Invalid characters in username")
        return v
```

**Use parameterized queries - ALWAYS:**
```python
# WRONG - SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# CORRECT - parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

**Sanitize for output context:**
```python
import html
from markupsafe import escape

# HTML context
safe_html = html.escape(user_input)

# Template context (Jinja2)
safe_template = escape(user_input)

# Shell context - avoid if possible, use subprocess with list args
import subprocess
subprocess.run(["ls", "-la", safe_path], check=True)  # NOT shell=True
```

### Authentication & Password Security

**Use modern password hashing:**
```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hash: str) -> bool:
    try:
        ph.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False
```

**Algorithm preference (2024-2025):**
1. Argon2id (recommended)
2. bcrypt (acceptable, widely supported)
3. scrypt (acceptable)
4. PBKDF2 (legacy, avoid for new systems)

**JWT best practices:**
```python
import jwt
from datetime import datetime, timedelta, UTC

def create_token(user_id: str, secret: str) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),  # Short expiry
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        },
        secret,
        algorithm="HS256"  # Use RS256 for distributed systems
    )

def verify_token(token: str, secret: str) -> dict:
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],  # Explicit algorithm list
        options={"require": ["exp", "iat", "sub"]}
    )
```

### SSH & Connection Security

**SSH key requirements:**
- Minimum 4096-bit RSA or Ed25519 (preferred)
- Passphrase-protected private keys
- Separate keys per environment/purpose
- Regular rotation (90 days recommended)

**SSH connection hardening:**
```python
import paramiko

def create_secure_client() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    # Verify host keys - NEVER use AutoAddPolicy in production
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    return client

# Connection with timeout and keepalive
client.connect(
    hostname=host,
    username=user,
    key_filename=key_path,
    timeout=30,
    banner_timeout=30,
    auth_timeout=30,
)
transport = client.get_transport()
transport.set_keepalive(60)
```

### Dependency Security

**Pin dependencies with hashes:**
```toml
# pyproject.toml
[tool.uv]
resolution = "locked"

# Or use pip-compile with hashes
# pip-compile --generate-hashes requirements.in
```

**Audit dependencies regularly:**
```bash
# Using pip-audit
pip-audit --strict

# Using safety
safety check

# Using uv
uv pip audit
```

**Supply chain attack mitigations:**
1. Pin exact versions in production
2. Use lock files (uv.lock, poetry.lock)
3. Verify package checksums
4. Monitor for typosquatting (check package names carefully)
5. Use private PyPI mirrors for critical deployments
6. Enable 2FA on PyPI accounts

### Logging Security

**Never log sensitive data:**
```python
import logging
import re
from typing import Any

class SensitiveDataFilter(logging.Filter):
    PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'password=***'),
        (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'api_key=***'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'secret=***'),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '<email>'),
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '<ssn>'),  # SSN
        (re.compile(r'\b\d{16}\b'), '<card>'),  # Credit card
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True
```

**Structured logging with redaction:**
```python
import structlog

def redact_sensitive(_, __, event_dict: dict) -> dict:
    sensitive_keys = {"password", "secret", "token", "api_key", "authorization"}
    for key in event_dict:
        if any(s in key.lower() for s in sensitive_keys):
            event_dict[key] = "***REDACTED***"
    return event_dict

structlog.configure(
    processors=[
        redact_sensitive,
        structlog.processors.JSONRenderer()
    ]
)
```

### Error Handling Security

**Never expose internal details:**
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def secure_endpoint(user_id: str):
    try:
        return get_user_data(user_id)
    except DatabaseError as e:
        # Log full details internally
        logger.exception("Database error for user %s", user_id)
        # Return generic message to client
        raise HTTPException(status_code=500, detail="Internal server error")
    except PermissionError:
        # Don't reveal if user exists
        raise HTTPException(status_code=404, detail="Resource not found")
```

### Cryptography

**Use high-level libraries:**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,  # OWASP 2024 recommendation
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_data(data: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data)
```

**Never implement your own crypto. Use:**
- `cryptography` library for encryption
- `secrets` module for random generation
- `hashlib` only for non-security hashing

## Anti-Patterns to Avoid

### Credential Anti-Patterns
- ❌ Hardcoded secrets in source code
- ❌ Secrets in version control (even in "private" repos)
- ❌ Shared credentials across environments
- ❌ Long-lived API keys without rotation
- ❌ Storing passwords in plaintext or reversible encryption
- ❌ Using MD5/SHA1 for password hashing

### Input Handling Anti-Patterns
- ❌ String concatenation for SQL queries
- ❌ `eval()` or `exec()` on user input
- ❌ `shell=True` in subprocess calls
- ❌ Trusting client-side validation alone
- ❌ Deserializing untrusted data with pickle
- ❌ Using `yaml.load()` instead of `yaml.safe_load()`

### Authentication Anti-Patterns
- ❌ Rolling your own authentication system
- ❌ Storing session tokens in localStorage (use httpOnly cookies)
- ❌ Long JWT expiration times (>1 hour for access tokens)
- ❌ Not validating JWT algorithm (algorithm confusion attacks)
- ❌ Password length limits under 64 characters
- ❌ Blocking paste in password fields

### Logging Anti-Patterns
- ❌ Logging full request/response bodies
- ❌ Logging authentication tokens
- ❌ Logging PII without masking
- ❌ Insufficient logging (can't detect attacks)
- ❌ Logs accessible without authentication

### Dependency Anti-Patterns
- ❌ Using `*` or unpinned versions in production
- ❌ Ignoring security advisories
- ❌ Installing packages from untrusted sources
- ❌ Not auditing transitive dependencies
- ❌ Running as root in containers

## Implementation Guidelines

### Step 1: Secure Development Environment
```bash
# Install security tools
uv add --dev bandit safety pip-audit ruff mypy

# Configure pre-commit hooks
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
  - repo: https://github.com/pyupio/safety
    rev: 2.3.5
    hooks:
      - id: safety
EOF
```

### Step 2: Configure Security Scanning
```toml
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101"]  # Skip assert warnings in tests only

[tool.ruff.lint]
select = ["S"]  # Enable security rules
```

### Step 3: Implement Security Middleware
```python
from starlette.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

middleware = [
    Middleware(HTTPSRedirectMiddleware),
    Middleware(TrustedHostMiddleware, allowed_hosts=["example.com"]),
]
```

### Step 4: Security Headers
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Step 5: Regular Security Audits
```bash
# Weekly dependency audit
pip-audit --strict --desc

# Static analysis
bandit -r src/ -f json -o bandit-report.json

# Check for known vulnerabilities
safety check --full-report
```

## Success Metrics

### Quantitative Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Critical vulnerabilities | 0 | Dependency audit |
| High vulnerabilities | 0 | Dependency audit |
| Bandit findings (high) | 0 | Static analysis |
| Secrets in code | 0 | git-secrets/trufflehog |
| Password hash strength | Argon2id | Code review |
| JWT expiry | ≤1 hour | Configuration audit |
| Dependency freshness | <30 days | Automated checks |

### Qualitative Metrics
- All secrets managed via secrets manager
- Input validation on all external boundaries
- Parameterized queries for all database access
- Security headers on all HTTP responses
- Audit logging for authentication events
- Regular penetration testing (quarterly)

### Monitoring & Alerting
- Failed authentication attempts (>5/minute = alert)
- Unusual API access patterns
- Dependency vulnerability notifications
- Certificate expiration warnings (30 days)
- Privilege escalation attempts

## Sources & References

[OWASP Top 10 2024](https://owasp.org/Top10/) — Industry standard web application security risks

[Python Security Best Practices - Black Duck](https://www.blackduck.com/blog/python-security-best-practices.html) — Six essential Python security practices

[Secrets Management Best Practices 2025 - Infisical](https://infisical.com/blog/secrets-management-best-practices) — Dynamic credentials and secrets lifecycle

[SSH Key Management - Keeper Security](https://www.keepersecurity.com/blog/2024/03/27/how-to-manage-ssh-keys/) — SSH key management best practices

[Supply Chain Security - Trail of Bits](https://blog.trailofbits.com/2025/09/24/supply-chain-attacks-are-exploiting-our-assumptions/) — Supply chain attack patterns and mitigations

[FastAPI Security - OAuth2 JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — JWT authentication implementation

[Python Authorization Best Practices - WorkOS](https://workos.com/blog/python-authorization-best-practices) — Authorization patterns for Python

[Input Validation - Pydantic](https://docs.pydantic.dev/latest/) — Data validation using Python type annotations

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version - comprehensive security best practices for Python applications
