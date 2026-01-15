---
title:        Rest Api Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15
status:       active
---

# Rest Api Best Practices

## Core Principles

### 1. Statelessness
Each request must contain all information needed to understand and complete it. The server stores no client context between requests, dramatically improving scalability and reliability.

### 2. Resource-Oriented Design
Focus on nouns (resources) rather than actions (verbs). Resources are identified by unique URLs and manipulated using standard HTTP methods, creating predictable, intuitive APIs.

### 3. Uniform Interface
Maintain consistent resource identification, standard HTTP methods, and predictable response structures across all endpoints. This consistency reduces cognitive load for API consumers.

### 4. Client-Server Separation
Decouple client and server concerns, allowing independent evolution of each. Servers provide data and business logic; clients handle presentation and user interaction.

### 5. Cacheability
Design responses to be explicitly cacheable or non-cacheable. Proper caching reduces server load, improves performance, and enhances scalability.

## Essential Practices

### HTTP Methods and Semantics

Use HTTP methods according to their intended semantics:

- **GET**: Retrieve data (safe, idempotent, cacheable)
- **POST**: Create new resources (not idempotent)
- **PUT**: Replace entire resource (idempotent)
- **PATCH**: Apply partial modifications (idempotent)
- **DELETE**: Remove resource (idempotent)

Violating these conventions creates unexpected side effects, such as GET requests accidentally modifying data.

### Resource Naming Conventions

```
# Good - Plural nouns, hierarchical structure
GET    /api/v1/users
GET    /api/v1/users/123
GET    /api/v1/users/123/orders
POST   /api/v1/users
PUT    /api/v1/users/123
DELETE /api/v1/users/123

# Bad - Verbs, inconsistent pluralization
GET    /api/v1/getUser/123
POST   /api/v1/createUser
GET    /api/v1/user/123/order
```

**Rules**:
- Use plural nouns for collections (`/users`, not `/user`)
- Use lowercase with hyphens for multi-word resources (`/order-items`)
- Nest resources to show relationships (`/users/123/orders`)
- Avoid verbs in URLs (use HTTP methods instead)
- Keep URLs short and intuitive

### Versioning Strategies

**URI Path Versioning** (Recommended for public APIs):
```
GET /api/v1/users
GET /api/v2/users
```

**Advantages**: Clear, cache-friendly, easy to route, visible in logs  
**Use when**: Building public APIs, need simple client integration

**Header-Based Versioning**:
```
GET /api/users
Accept: application/vnd.myapi.v2+json
```

**Advantages**: Clean URLs, fine-grained control, adheres to REST principles  
**Use when**: Internal systems, need content negotiation

**Best Practices**:
- Choose one strategy and stick to it
- Use semantic versioning (v1, v2, v3)
- Run versions in parallel during migration
- Send `Deprecation` and `Sunset` headers for old versions
- Provide migration guides for breaking changes
- Maintain backward compatibility within major versions

### Authentication and Authorization

**Modern Standards (2025)**:

1. **OAuth 2.0 + OpenID Connect**: Industry standard for delegated authorization
   - Use for third-party integrations
   - Supports multiple grant types
   - Provides token refresh mechanisms

2. **JWT (JSON Web Tokens)**: Stateless authentication
   - Self-contained tokens with claims
   - No server-side session storage
   - Include expiration (`exp`) and issuer (`iss`) claims

3. **API Keys**: Simple authentication for service-to-service
   - Use for internal services or trusted partners
   - Rotate keys regularly
   - Never expose in URLs (use headers)

**Security Requirements**:
- **Never use Basic Authentication** in production (credentials sent with every request)
- **Always use HTTPS/TLS** for encrypted transport
- **Implement Role-Based Access Control (RBAC)** for authorization
- **Validate all inputs** to prevent injection attacks
- **Use short-lived tokens** with refresh mechanisms
- **Store secrets securely** (environment variables, key vaults)

**Headers**:
```
Authorization: Bearer <jwt-token>
X-API-Key: <api-key>
```

### Error Handling and Status Codes

**Use Accurate HTTP Status Codes**:

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Authentication required/failed |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server failure |
| 503 | Service Unavailable | Temporary outage, include `Retry-After` |

**Structured Error Responses** (RFC 9457 - Problem Details):

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "The email field is required",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "message": "Email is required",
      "code": "REQUIRED_FIELD"
    }
  ],
  "timestamp": "2026-01-15T14:30:00Z",
  "trace_id": "abc123xyz"
}
```

**Error Message Guidelines**:
- Be clear and actionable
- Include field-level details for validation errors
- Provide error codes for programmatic handling
- Never expose sensitive information (stack traces, internal paths)
- Include trace IDs for debugging
- Use consistent error structure across all endpoints

**Validation Errors**:
- Use 422 for field-level validation failures
- Use 400 for malformed payloads (invalid JSON)
- Provide specific field names and error messages

### Pagination, Filtering, and Sorting

**Pagination** (Required from day one):

**Cursor-Based Pagination** (Recommended):
```
GET /api/v1/users?cursor=eyJpZCI6MTIzfQ&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true
  }
}
```

**Advantages**: Efficient for large datasets, handles real-time data, no page drift  
**Use when**: Data changes frequently, need consistent results

**Offset-Based Pagination**:
```
GET /api/v1/users?page=2&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 1000,
    "total_pages": 50
  }
}
```

**Advantages**: Simple, allows jumping to specific pages  
**Use when**: Static data, need page numbers

**Best Practices**:
- Set maximum limit (cap at 100-1000)
- Use stable, indexed sort keys for cursors
- Return metadata (`total_count`, `next_cursor`, `has_more`)
- Use `Link` header for navigation (first, last, next, prev)

**Filtering**:
```
GET /api/v1/users?status=active&role=admin
GET /api/v1/products?price_min=10&price_max=100
GET /api/v1/orders?created_after=2026-01-01
```

**Sorting**:
```
GET /api/v1/users?sort=created_at:desc
GET /api/v1/products?sort=price:asc,name:asc
```

**Guidelines**:
- Use query parameters for filtering and sorting
- Support multiple sort fields
- Document available filter fields
- Validate filter values
- Use consistent naming (snake_case or camelCase)

### Rate Limiting and Throttling

**Rate Limiting Algorithms**:

| Algorithm | Best For | How It Works |
|-----------|----------|--------------|
| Fixed Window | Simple traffic patterns | Resets at fixed intervals |
| Sliding Window | Smooth traffic control | Uses rolling time windows |
| Token Bucket | Handling bursts | Refills tokens over time |
| Leaky Bucket | Consistent flow | Processes at steady rate |

**Implementation**:
```
# Response Headers
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642089600
Retry-After: 3600

# 429 Response
HTTP/1.1 429 Too Many Requests
{
  "error": "Rate limit exceeded",
  "limit": 1000,
  "window": "1 hour",
  "retry_after": 3600
}
```

**Best Practices**:
- Set limits per user/API key, not just IP
- Use 429 status code for rate limit violations
- Include rate limit headers in all responses
- Implement tiered limits (free vs. paid)
- Track metrics: request patterns, error rates, data volume
- Use dynamic rate limiting based on server load
- Leverage caching (Redis, CDN) to reduce redundant requests
- Consider API management platforms for advanced features

**Typical Limits**:
- Public APIs: 100-1000 requests/hour
- Authenticated users: 5000-10000 requests/hour
- Premium tiers: Higher or unlimited

### API Documentation

**OpenAPI/Swagger Specification** (Industry Standard):

```yaml
openapi: 3.1.0
info:
  title: User Management API
  version: 1.0.0
  description: API for managing users
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
```

**Documentation Requirements**:
- **Interactive documentation**: Swagger UI, Redoc, or similar
- **Code examples**: Multiple languages (curl, Python, JavaScript)
- **Authentication guide**: How to obtain and use credentials
- **Error catalog**: All possible error codes and meanings
- **Rate limits**: Clearly documented limits and headers
- **Changelog**: Version history and migration guides
- **Sandbox environment**: Test API without affecting production

**Tools**:
- **Swagger/OpenAPI**: Standard specification and tooling
- **Postman**: API testing and documentation
- **Redoc**: Beautiful OpenAPI documentation
- **API Blueprint**: Alternative specification format

### Performance Optimization

**Caching Strategies**:
```
# Response Headers
Cache-Control: public, max-age=3600
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Wed, 15 Jan 2026 14:30:00 GMT

# Conditional Requests
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
If-Modified-Since: Wed, 15 Jan 2026 14:30:00 GMT
```

**Best Practices**:
- Use `Cache-Control` headers appropriately
- Implement ETags for conditional requests
- Return 304 Not Modified when content unchanged
- Cache at multiple levels (CDN, API gateway, application)
- Invalidate caches on updates

**Payload Optimization**:
- Use compression (gzip, brotli)
- Support field selection (`?fields=id,name,email`)
- Implement sparse fieldsets (JSON:API)
- Avoid over-fetching with GraphQL-style queries
- Use pagination to limit response size

**Database Optimization**:
- Index frequently queried fields
- Use database connection pooling
- Implement query result caching
- Avoid N+1 queries
- Use database read replicas for GET requests

### HATEOAS and Hypermedia

**Hypermedia as the Engine of Application State**:

```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "_links": {
    "self": {
      "href": "/api/v1/users/123"
    },
    "orders": {
      "href": "/api/v1/users/123/orders"
    },
    "update": {
      "href": "/api/v1/users/123",
      "method": "PUT"
    },
    "delete": {
      "href": "/api/v1/users/123",
      "method": "DELETE"
    }
  }
}
```

**Benefits**:
- Self-documenting API
- Clients discover available actions
- Reduces coupling between client and server
- Enables API evolution without breaking clients

**When to Use**:
- Public APIs with diverse clients
- Long-lived APIs requiring flexibility
- APIs where discoverability is important

### Content Negotiation

```
# Request
Accept: application/json
Accept-Language: en-US
Accept-Encoding: gzip, deflate

# Response
Content-Type: application/json; charset=utf-8
Content-Language: en-US
Content-Encoding: gzip
```

**Support Multiple Formats**:
- JSON (default, most common)
- XML (legacy systems)
- CSV (data export)
- Protocol Buffers (high performance)

**Best Practices**:
- Default to JSON if no `Accept` header
- Return 406 Not Acceptable for unsupported formats
- Use proper MIME types
- Support compression for large responses

## Anti-Patterns to Avoid

### 1. Ignoring HTTP Semantics
**Bad**: Using POST for all operations, including reads  
**Good**: Use GET for reads, POST for creates, PUT/PATCH for updates

### 2. Exposing Internal Implementation
**Bad**: `/api/database/users_table`  
**Good**: `/api/users`

### 3. Inconsistent Naming
**Bad**: `/getUsers`, `/user/create`, `/deleteUser`  
**Good**: `GET /users`, `POST /users`, `DELETE /users/{id}`

### 4. Returning 200 for Errors
**Bad**: `200 OK` with `{"error": "User not found"}`  
**Good**: `404 Not Found` with proper error structure

### 5. No Versioning Strategy
**Bad**: Breaking changes without version increments  
**Good**: Clear versioning with migration paths

### 6. Overly Chatty APIs
**Bad**: Requiring 10 requests to load one page  
**Good**: Batch endpoints, compound documents, or GraphQL

### 7. Missing Rate Limits
**Bad**: Unlimited requests leading to abuse  
**Good**: Documented rate limits with 429 responses

### 8. Poor Error Messages
**Bad**: `{"error": "Invalid input"}`  
**Good**: Specific field errors with codes and suggestions

### 9. Ignoring Security
**Bad**: No authentication, HTTP instead of HTTPS  
**Good**: OAuth 2.0, HTTPS, input validation, RBAC

### 10. No Documentation
**Bad**: Undocumented endpoints, unclear parameters  
**Good**: OpenAPI spec, interactive docs, code examples

### 11. Synchronous Long Operations
**Bad**: 60-second timeout waiting for job completion  
**Good**: Async pattern with 202 Accepted and status endpoint

### 12. Exposing Database IDs
**Bad**: Sequential IDs revealing business metrics  
**Good**: UUIDs or opaque identifiers

### 13. No Pagination
**Bad**: Returning 100,000 records in one response  
**Good**: Cursor or offset pagination from day one

### 14. Ignoring Idempotency
**Bad**: POST creating duplicate resources on retry  
**Good**: Idempotency keys for safe retries

## Implementation Guidelines

### Step 1: Design First (API-First Approach)

1. **Define resources and relationships**
   - Identify domain entities
   - Map relationships (one-to-many, many-to-many)
   - Design URL hierarchy

2. **Create OpenAPI specification**
   - Document all endpoints
   - Define request/response schemas
   - Specify authentication requirements

3. **Review with stakeholders**
   - Get feedback from API consumers
   - Validate use cases
   - Iterate on design

4. **Generate documentation and mocks**
   - Use Swagger UI for interactive docs
   - Create mock servers for early testing
   - Share with frontend teams

### Step 2: Implement Core Functionality

1. **Set up framework and middleware**
   - Choose REST framework (Express, FastAPI, Spring Boot)
   - Configure CORS, compression, logging
   - Set up error handling middleware

2. **Implement authentication/authorization**
   - Integrate OAuth 2.0 or JWT
   - Set up RBAC or ABAC
   - Secure all endpoints

3. **Build resource endpoints**
   - Follow RESTful conventions
   - Implement proper HTTP methods
   - Add input validation

4. **Add pagination, filtering, sorting**
   - Implement cursor-based pagination
   - Support common filters
   - Allow flexible sorting

### Step 3: Add Cross-Cutting Concerns

1. **Rate limiting**
   - Choose algorithm (token bucket recommended)
   - Set appropriate limits
   - Add rate limit headers

2. **Caching**
   - Implement Cache-Control headers
   - Add ETag support
   - Configure CDN if applicable

3. **Logging and monitoring**
   - Log all requests with trace IDs
   - Track error rates and latency
   - Set up alerts for anomalies

4. **Security hardening**
   - Enable HTTPS only
   - Add security headers (HSTS, CSP)
   - Implement input sanitization
   - Set up WAF if needed

### Step 4: Testing and Validation

1. **Unit tests**
   - Test business logic
   - Mock external dependencies
   - Aim for 80%+ coverage

2. **Integration tests**
   - Test full request/response cycle
   - Validate authentication flows
   - Test error scenarios

3. **Contract tests**
   - Validate against OpenAPI spec
   - Ensure backward compatibility
   - Test with consumer-driven contracts

4. **Performance tests**
   - Load testing with realistic traffic
   - Identify bottlenecks
   - Validate rate limiting

### Step 5: Documentation and Release

1. **Complete documentation**
   - Publish OpenAPI spec
   - Add code examples
   - Create getting started guide

2. **Versioning and changelog**
   - Tag release version
   - Document breaking changes
   - Provide migration guide

3. **Monitoring and observability**
   - Set up dashboards
   - Configure alerts
   - Track key metrics

4. **Feedback loop**
   - Collect API usage metrics
   - Gather developer feedback
   - Plan improvements

## Success Metrics

### Performance Metrics
- **Response time**: p50, p95, p99 latency
  - Target: p95 < 200ms for simple queries
- **Throughput**: Requests per second
  - Target: Based on expected load + 50% buffer
- **Error rate**: Percentage of 5xx responses
  - Target: < 0.1%
- **Availability**: Uptime percentage
  - Target: 99.9% (8.76 hours downtime/year)

### Developer Experience Metrics
- **Time to first successful call**: How quickly developers can make their first API call
  - Target: < 15 minutes
- **Documentation completeness**: Percentage of endpoints documented
  - Target: 100%
- **API adoption rate**: Number of active integrations
- **Developer satisfaction**: Survey scores
  - Target: > 4.0/5.0

### Business Metrics
- **API usage growth**: Month-over-month increase
- **Integration success rate**: Percentage of started integrations completed
  - Target: > 80%
- **Support ticket volume**: API-related issues
  - Target: Decreasing trend
- **Time to resolve issues**: Average resolution time
  - Target: < 24 hours

### Security Metrics
- **Authentication failures**: Rate of failed auth attempts
- **Rate limit violations**: Frequency of 429 responses
- **Security incidents**: Number of breaches or vulnerabilities
  - Target: 0
- **Time to patch vulnerabilities**: Average time to fix
  - Target: < 7 days for critical

### Quality Metrics
- **Breaking changes**: Number per release
  - Target: 0 within major versions
- **Backward compatibility**: Percentage of old clients still working
  - Target: 100% within major version
- **Test coverage**: Percentage of code covered
  - Target: > 80%
- **API consistency**: Adherence to design standards
  - Target: 100% compliance

## Sources & References

[1] API Design Best Practices: Building Scalable REST APIs in 2026 - https://hakia.com/engineering/api-design-best-practices/

[2] REST API Best Practices and Standards in 2026 - https://hevodata.com/learn/rest-api-best-practices/

[3] 10 Essential RESTful API Best Practices for 2025 - https://dotmock.com/blog/restful-api-best-practices

[4] 10 Essential API Development Best Practices for Scalable Systems in 2025 - https://group107.com/blog/api-development-best-practices/

[5] Mastering API Versioning: Strategies, Trade‑offs, and Best Practices - https://nerdleveltech.com/mastering-api-versioning-strategies-tradeoffs-and-best-practices

[6] Api Versioning Best Practices: Top Strategies for 2025 - https://www.docuwriter.ai/posts/api-versioning-best-practices

[7] 10 Essential REST API Security Best Practices for 2025 - https://group107.com/blog/rest-api-security-best-practices/

[8] Best Practices for Secure API Authentication in 2025 - https://techlasi.com/savvy/best-practices-for-secure-api-authentication/

[9] Best Practices for Consistent API Error Handling - https://zuplo.com/blog/2025/02/11/best-practices-for-api-error-handling

[10] A Practical Guide to API Error Handling - https://www.caduh.com/blog/practical-guide-to-api-error-handling

[11] Pagination, Filtering & Sorting - https://www.juheapi.com/blog/pagination-filtering-sorting-efficient-rest-apis

[12] REST API Response Pagination, Sorting and Filtering - https://restfulapi.net/api-pagination-sorting-filtering/

[13] Interactive API Documentation Made Easy with OpenAPI - https://leapcell.io/blog/interactive-api-documentation-made-easy-with-openapi

[14] OpenAPI and Swagger: Automating Your API Documentation - https://www.juheapi.com/blog/openapi-and-swagger-automated-api-documentation

[15] 10 Best Practices for API Rate Limiting in 2025 - https://zuplo.com/blog/2025/01/06/10-best-practices-for-api-rate-limiting-in-2025

[16] API Throttling Best Practices & Techniques for Peak Performance - https://www.gravitee.io/blog/api-throttling-best-practices

## Version History

- v1.0 (2026-01-15): Initial version based on 2025-2026 REST API best practices research
