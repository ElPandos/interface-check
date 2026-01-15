---
title:        Rest Api Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 14:54:52
status:       active
---

# Rest Api Patterns

## Core Principles

### 1. Resource-Oriented Design
REST APIs center on resources (nouns) rather than actions (verbs). Resources represent entities in your system and are manipulated using standard HTTP methods. This creates predictable, intuitive interfaces that leverage web architecture.

### 2. Stateless Communication
Each request contains all information needed for processing. The server maintains no client session state between requests, enabling horizontal scaling and simplifying architecture.

### 3. Standard HTTP Semantics
Leverage HTTP methods, status codes, and headers correctly. GET retrieves, POST creates, PUT replaces, PATCH modifies, DELETE removes. Status codes communicate outcomes: 2xx success, 4xx client errors, 5xx server errors.

### 4. Uniform Interface
Consistent patterns across all endpoints reduce cognitive load. Use predictable naming conventions, error formats, and response structures throughout the API.

### 5. Hierarchical Resource Relationships
URI structure reflects logical relationships between resources. Parent-child relationships appear in paths (e.g., `/users/{userId}/orders/{orderId}`), conveying semantic meaning and dependencies.

## Essential Patterns

### Resource Naming Conventions

**Use Plural Nouns for Collections**
```
GET    /users              # List all users
POST   /users              # Create new user
GET    /users/{id}         # Get specific user
PUT    /users/{id}         # Replace user
PATCH  /users/{id}         # Update user fields
DELETE /users/{id}         # Remove user
```

**Lowercase with Hyphens**
```
/user-profiles           # Correct
/userProfiles            # Avoid camelCase
/user_profiles           # Avoid underscores
```

**Hierarchical Relationships**
```
/users/{userId}/orders                    # User's orders
/users/{userId}/orders/{orderId}          # Specific order
/users/{userId}/orders/{orderId}/items    # Order items
```

**Avoid Verbs in URIs**
```
POST /users              # Correct
POST /createUser         # Wrong - verb in URI
GET  /users/{id}         # Correct
GET  /getUser?id=123     # Wrong - action in path
```

### HTTP Method Usage

| Method | Purpose | Idempotent | Safe | Request Body | Response Body |
|--------|---------|------------|------|--------------|---------------|
| GET | Retrieve resource(s) | Yes | Yes | No | Yes |
| POST | Create resource | No | No | Yes | Yes (created resource) |
| PUT | Replace entire resource | Yes | No | Yes | Yes (updated resource) |
| PATCH | Partial update | No | No | Yes | Yes (updated resource) |
| DELETE | Remove resource | Yes | No | Optional | Optional |

**Idempotency**: Multiple identical requests produce same result as single request.
**Safety**: Operation causes no side effects on server state.

### HTTP Status Codes

**Success (2xx)**
- `200 OK`: Successful GET, PUT, PATCH, or DELETE
- `201 Created`: Successful POST creating new resource (include Location header)
- `204 No Content`: Successful request with no response body (often DELETE)

**Client Errors (4xx)**
- `400 Bad Request`: Malformed request syntax or invalid data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Authenticated but lacks permission
- `404 Not Found`: Resource does not exist
- `405 Method Not Allowed`: HTTP method not supported for resource
- `409 Conflict`: Request conflicts with current state (e.g., duplicate)
- `422 Unprocessable Entity`: Validation errors in request data
- `429 Too Many Requests`: Rate limit exceeded

**Server Errors (5xx)**
- `500 Internal Server Error`: Unexpected server failure
- `502 Bad Gateway`: Invalid response from upstream server
- `503 Service Unavailable`: Temporary overload or maintenance
- `504 Gateway Timeout`: Upstream server timeout

### Error Response Structure

Follow RFC 9457 Problem Details standard for consistent, actionable error responses:

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Email address format is invalid",
  "instance": "/users/create",
  "errors": [
    {
      "field": "email",
      "message": "Must be valid email format",
      "code": "INVALID_EMAIL_FORMAT"
    }
  ],
  "timestamp": "2026-01-15T14:54:52Z",
  "request_id": "abc123-def456"
}
```

**Key Elements**:
- `type`: URI identifying error type (for documentation)
- `title`: Human-readable summary
- `status`: HTTP status code
- `detail`: Specific explanation for this occurrence
- `instance`: URI of request that caused error
- `errors`: Array of field-level validation errors
- `timestamp`: When error occurred
- `request_id`: Correlation ID for debugging

**Security Considerations**:
- Never expose stack traces or internal paths
- Avoid revealing system architecture details
- Provide helpful messages without security risks
- Log detailed errors server-side, return sanitized versions to clients

### Versioning Strategies

**URI Path Versioning (Most Common)**
```
/v1/users
/v2/users
```
**Pros**: Simple, explicit, cache-friendly, visible in URLs
**Cons**: Violates REST principle of resource identity stability

**Header Versioning**
```
GET /users
Accept: application/vnd.api.v2+json
```
**Pros**: Clean URIs, follows REST principles
**Cons**: Less visible, harder to test in browsers

**Query Parameter Versioning**
```
/users?version=2
```
**Pros**: Simple, backward compatible
**Cons**: Pollutes query space, less discoverable

**Content Negotiation**
```
GET /users
Accept: application/vnd.api+json; version=2
```
**Pros**: RESTful, flexible
**Cons**: Complex, requires client sophistication

**Best Practices**:
- Use semantic versioning (v1, v2, not v1.2.3 in URI)
- Version only when breaking changes occur
- Maintain backward compatibility within major versions
- Deprecate old versions gradually with clear timelines
- Document migration paths between versions

### Pagination Patterns

**Offset/Limit (Simple)**
```
GET /users?offset=20&limit=10
```
**Response**:
```json
{
  "data": [...],
  "pagination": {
    "offset": 20,
    "limit": 10,
    "total": 150
  }
}
```
**Pros**: Easy to implement, supports jumping to arbitrary pages
**Cons**: Performance degrades with large offsets, unstable when data changes

**Cursor-Based (Scalable)**
```
GET /users?cursor=eyJpZCI6MTIzfQ==&limit=10
```
**Response**:
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTMzfQ==",
    "has_more": true
  }
}
```
**Pros**: Consistent performance, stable pagination, handles real-time data
**Cons**: Cannot jump to arbitrary pages, more complex implementation

**Best Practices**:
- Set maximum limit (e.g., 100) to prevent abuse
- Default to reasonable page size (e.g., 20)
- Use cursor-based for large datasets or real-time feeds
- Include metadata: `total_count`, `has_more`, `next_cursor`
- Use stable, indexed sort keys for cursors

### Filtering and Sorting

**Filtering**
```
GET /users?status=active&role=admin
GET /products?price_min=10&price_max=100
GET /orders?created_after=2026-01-01
```

**Sorting**
```
GET /users?sort=created_at          # Ascending
GET /users?sort=-created_at         # Descending (minus prefix)
GET /users?sort=last_name,first_name # Multiple fields
```

**Best Practices**:
- Use query parameters for filtering and sorting
- Support common operators: `_min`, `_max`, `_gt`, `_lt`, `_contains`
- Document available filter fields and operators
- Validate filter values to prevent injection attacks
- Index frequently filtered/sorted fields

### HATEOAS (Hypermedia as the Engine of Application State)

Include links to related resources and available actions:

```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "_links": {
    "self": { "href": "/users/123" },
    "orders": { "href": "/users/123/orders" },
    "edit": { "href": "/users/123", "method": "PUT" },
    "delete": { "href": "/users/123", "method": "DELETE" }
  }
}
```

**Benefits**:
- Self-documenting API
- Clients discover available actions dynamically
- Reduces coupling between client and server
- Enables API evolution without breaking clients

### Authentication and Authorization

**Bearer Token (OAuth 2.0, JWT)**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**API Key**
```
X-API-Key: your-api-key-here
```

**Best Practices**:
- Use HTTPS for all API endpoints
- Return `401 Unauthorized` for missing/invalid authentication
- Return `403 Forbidden` for insufficient permissions
- Implement rate limiting per user/API key
- Use short-lived tokens with refresh mechanism
- Never log or expose credentials in responses

### Rate Limiting

**Headers**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642089600
Retry-After: 3600
```

**Response (429 Too Many Requests)**
```json
{
  "type": "https://api.example.com/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "API rate limit of 1000 requests per hour exceeded",
  "retry_after": 3600
}
```

### Caching

**Response Headers**
```
Cache-Control: public, max-age=3600
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Wed, 15 Jan 2026 14:00:00 GMT
```

**Conditional Requests**
```
GET /users/123
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

Response: 304 Not Modified (if unchanged)
```

**Best Practices**:
- Use ETags for resource versioning
- Set appropriate `Cache-Control` directives
- Support conditional requests (`If-None-Match`, `If-Modified-Since`)
- Cache GET requests, never cache POST/PUT/PATCH/DELETE
- Use `Vary` header when response depends on request headers

## Anti-Patterns to Avoid

### 1. RPC-Style Endpoints
**Wrong**: `/getUserById`, `/createOrder`, `/updateProfile`
**Right**: `GET /users/{id}`, `POST /orders`, `PATCH /profile`

**Problem**: Exposes implementation details, ignores HTTP semantics, creates rigid interfaces.

### 2. Verbs in Resource URIs
**Wrong**: `/api/getUsers`, `/api/deleteUser/123`
**Right**: `GET /users`, `DELETE /users/123`

**Problem**: Redundant with HTTP methods, violates resource-oriented design.

### 3. Misusing HTTP Methods
**Wrong**: `GET /users/delete?id=123` (side effects in GET)
**Wrong**: `POST /users/123` (update using POST instead of PUT/PATCH)

**Problem**: Breaks HTTP semantics, prevents caching, confuses clients.

### 4. Inconsistent Status Codes
**Wrong**: Returning `200 OK` with error message in body
**Wrong**: Using `500` for validation errors (should be `400` or `422`)

**Problem**: Forces clients to parse response bodies to detect errors, breaks HTTP conventions.

### 5. Ignoring Idempotency
**Wrong**: POST request that creates duplicate resources on retry
**Wrong**: PUT/DELETE that fails differently on subsequent calls

**Problem**: Network retries cause unintended side effects, data corruption.

### 6. Overfetching/Underfetching
**Wrong**: Returning entire user object when only name needed
**Wrong**: Requiring multiple requests to assemble related data

**Solution**: Support field selection (`?fields=name,email`) and resource expansion (`?expand=orders`).

### 7. Breaking Changes Without Versioning
**Wrong**: Removing fields, changing data types, or altering behavior without version bump

**Problem**: Breaks existing clients without warning, violates API contracts.

### 8. Exposing Internal Implementation
**Wrong**: Database IDs as primary keys, internal error messages, stack traces
**Wrong**: URIs reflecting database structure (`/tables/users`)

**Problem**: Couples API to implementation, creates security risks, prevents refactoring.

### 9. Ignoring Security
**Wrong**: No authentication, HTTP instead of HTTPS, verbose error messages
**Wrong**: No rate limiting, accepting unbounded request sizes

**Problem**: Enables attacks, data breaches, denial of service.

### 10. Poor Error Messages
**Wrong**: Generic errors without details (`"Error occurred"`)
**Wrong**: Exposing stack traces or internal paths

**Problem**: Difficult to debug, security risks, poor developer experience.

### 11. Inconsistent Naming Conventions
**Wrong**: Mixing camelCase, snake_case, and kebab-case
**Wrong**: Singular and plural resource names inconsistently

**Problem**: Constant documentation lookups, broken expectations, more bugs.

### 12. Lack of Documentation
**Wrong**: No API documentation, outdated examples, missing error codes

**Problem**: Developers cannot use API effectively, increased support burden.

### 13. Ignoring Pagination
**Wrong**: Returning thousands of records in single response

**Problem**: Performance degradation, timeouts, excessive bandwidth usage.

### 14. Hidden Inter-Parameter Dependencies
**Wrong**: Parameters that only work together without documentation
**Wrong**: Conflicting parameters that silently override each other

**Problem**: Unpredictable behavior, difficult to use correctly.

## Implementation Guidelines

### Step 1: Design Resource Model
1. Identify core entities (users, orders, products)
2. Define relationships (one-to-many, many-to-many)
3. Map to URI hierarchy (`/users/{id}/orders`)
4. Choose primary identifiers (UUIDs vs integers)

### Step 2: Define URI Structure
1. Use plural nouns for collections
2. Use lowercase with hyphens
3. Reflect hierarchical relationships in paths
4. Keep URIs short and meaningful
5. Avoid file extensions (`.json`, `.xml`)

### Step 3: Map HTTP Methods to Operations
1. GET for retrieval (safe, idempotent)
2. POST for creation (non-idempotent)
3. PUT for full replacement (idempotent)
4. PATCH for partial updates
5. DELETE for removal (idempotent)

### Step 4: Implement Error Handling
1. Use appropriate HTTP status codes
2. Follow RFC 9457 Problem Details format
3. Include machine-readable error codes
4. Provide human-readable messages
5. Add request IDs for tracing
6. Log detailed errors server-side
7. Sanitize errors sent to clients

### Step 5: Add Pagination, Filtering, Sorting
1. Choose pagination strategy (offset vs cursor)
2. Set reasonable defaults and maximums
3. Support common filter operators
4. Allow sorting by multiple fields
5. Return pagination metadata

### Step 6: Implement Versioning
1. Choose versioning strategy (URI path recommended)
2. Use semantic versioning
3. Document breaking vs non-breaking changes
4. Maintain backward compatibility within versions
5. Provide deprecation notices and timelines

### Step 7: Secure the API
1. Require HTTPS for all endpoints
2. Implement authentication (OAuth 2.0, JWT)
3. Enforce authorization checks
4. Add rate limiting per user/key
5. Validate all inputs
6. Sanitize error messages
7. Use security headers (CORS, CSP)

### Step 8: Add Caching
1. Set `Cache-Control` headers appropriately
2. Generate ETags for resources
3. Support conditional requests
4. Use `Vary` header when needed
5. Cache only safe methods (GET, HEAD)

### Step 9: Document the API
1. Use OpenAPI/Swagger specification
2. Provide interactive documentation
3. Include code examples in multiple languages
4. Document all error codes and meanings
5. Explain authentication and authorization
6. Show pagination, filtering, sorting examples
7. Keep documentation synchronized with code

### Step 10: Monitor and Iterate
1. Track API usage metrics
2. Monitor error rates by endpoint
3. Measure response times
4. Collect client feedback
5. Version and evolve based on needs
6. Deprecate unused endpoints gracefully

## Success Metrics

### Performance Metrics
- **Response Time**: p50, p95, p99 latency by endpoint
- **Throughput**: Requests per second handled
- **Error Rate**: Percentage of 4xx and 5xx responses
- **Availability**: Uptime percentage (target: 99.9%+)

### Usage Metrics
- **Adoption Rate**: Number of active API consumers
- **Endpoint Popularity**: Most/least used endpoints
- **Version Distribution**: Clients per API version
- **Rate Limit Hits**: Frequency of 429 responses

### Quality Metrics
- **Time to First Hello World**: How quickly developers can make first successful call
- **Documentation Completeness**: Percentage of endpoints documented
- **Breaking Changes**: Frequency of backward-incompatible changes
- **Support Tickets**: API-related issues reported

### Developer Experience Metrics
- **API Consistency Score**: Adherence to naming conventions and patterns
- **Error Message Quality**: Percentage of errors with actionable details
- **Time to Resolution**: Average time to debug API issues
- **Client Satisfaction**: Survey scores from API consumers

### Business Metrics
- **API-Driven Revenue**: Revenue attributed to API usage
- **Partner Integrations**: Number of third-party integrations
- **Time to Market**: Speed of adding new API features
- **Cost per Request**: Infrastructure cost per API call

## Sources & References

[1] REST API Error Handling - https://josipmisko.com/posts/rest-api-error-handling
[2] 7 Response Errors - https://thejacksonlaboratory.github.io/api-standards/07-error-handling/
[3] REST API Status Code Design Guide - https://www.juheapi.com/blog/rest-api-error-handling-and-status-code-design-guide
[4] Best Practices, Code, & Analytics - https://www.elinext.com/blog/exception-handling-in-restful-apis/
[5] Essential Rest API Error Handling Best Practices - https://www.dhiwise.com/post/rest-api-error-handling-best-practices-for-developers
[6] Best Practices for REST API Error Handling Solutions - https://moldstud.com/articles/p-a-comprehensive-guide-to-rest-api-error-handling-best-practices-and-solutions
[7] Best Practices For REST API Error Handling - https://undercodetesting.com/best-practices-for-rest-api-error-handling/
[8] Best Practices for Consistent API Error Handling - https://zuplo.com/learning-center/best-practices-for-api-error-handling
[9] A Guide to API Design and Development - Status Codes and Error Handling - https://kindatechnical.com/api-design-development/lesson-13-status-codes-and-error-handling.html
[10] REST API Error Handling Best Practices and Solutions Guide - https://moldstud.com/articles/p-comprehensive-guide-to-rest-api-error-handling-best-practices-solutions
[11] Advanced API Design: Versioning, Pagination, and Error Handling - https://coderfacts.com/advanced-topics/api-design-versioning/
[12] Pagination, Filtering & Sorting - https://www.juheapi.com/blog/pagination-filtering-sorting-efficient-rest-apis
[13] REST API guidelines - https://www.ahlstrand.es/posts/rest-api-guidelines
[14] REST API Response Pagination, Sorting and Filtering - https://restfulapi.net/api-pagination-sorting-filtering/
[15] Mastering API Versioning: Strategies, Trade‑offs, and Best Practices - https://nerdleveltech.com/mastering-api-versioning-strategies-tradeoffs-and-best-practices
[16] Best Practices for Filtering, Searching, Sorting, Paging - https://rajasekar.dev/blog/api-design-filtering-searching-sorting-and-pagination
[17] What is API Versioning - Developer Reference - https://generalistprogrammer.com/glossary/api-versioning-strategies
[18] REST API Versioning Strategies A Deep Dive - https://toxigon.com/rest-api-versioning-strategies
[19] Mastering RESTful API Versioning Strategies - https://toxigon.com/restful-api-versioning-strategies
[20] API Versioning Strategies: A Practical Guide - https://hemaks.org/posts/api-versioning-strategies-a-practical-guide-to-managing-api-changes-without-breaking-the-internet/
[21] Avoid Pitfalls & Boost Performance - https://gist.ly/youtube-summarizer/mastering-rest-api-design-avoid-pitfalls-boost-performance
[22] Common Mistakes in RESTful API Design - https://zuplo.com/blog/2025/03/12/common-pitfalls-in-restful-api-design
[23] API Design Anti-patterns: Common Mistakes to Avoid in API Design - Xapi - https://blog.xapihub.io/2024/06/19/API-Design-Anti-patterns.html
[24] REST Anti-Patterns - http://www.infoq.com/articles/rest-anti-patterns
[25] API Design Anti-patterns: How to identify & avoid them - https://specmatic.io/appearance/how-to-identify-avoid-api-design-anti-patterns/
[26] REST API (anti)-patterns - https://blog.ptidej.net/rest-api-anti-patterns/
[27] A Guide to API Design and Development - Introduction to Anti-Patterns - https://kindatechnical.com/api-design-development/lesson-73-introduction-to-anti-patterns.html
[28] REST anti-patterns - https://marcelocure.medium.com/rest-anti-patterns-b128597f5430
[29] The 5 Most Common REST API Design Mistakes (and How to Avoid Them) - https://www.milanjovanovic.tech/blog/the-5-most-common-rest-api-design-mistakes-and-how-to-avoid-them
[30] 10 Common RESTful API Mistakes To Avoid - https://www.arunangshudas.com/blog/10-common-restful-api-mistakes-to-avoid/
[31] API Design Best Practices: Building Scalable REST APIs in 2025 - https://www.hakia.com/engineering/api-design-best-practices/
[32] REST API URI Naming Conventions and Best Practices - https://restfulapi.net/resource-naming/
[33] How to Choose the Right REST API Naming Conventions - https://zuplo.com/blog/how-to-choose-the-right-rest-api-naming-conventions
[34] Resource Naming and URL Structure - https://wisdom.gitbook.io/gyan/core/rest-apis-design/resource-naming-and-url-structure
[35] Rest Api Url Best Practices - https://www.restack.io/p/design-principles-for-ai-products-answer-rest-api-url-best-practices
[36] Crafting Effective REST API URL Naming Conventions - https://toxigon.com/rest-api-url-naming-conventions
[37] REST API Best Practices: A Comprehensive Guide - https://www.aubreyzulu.com/articles/rest-api-best-practices
[38] Rest Api Url Path Best Practices - https://www.restack.io/p/design-principles-for-ai-products-answer-rest-api-url-path-best-practices
[39] Introduction to REST API URL Design - https://dotnet.rest/docs/basics/concepts/url-design/
[40] RESTful API Resource Naming Guide (URI Naming) - https://dev.to/daryllukas/rest-api-resource-uri-naming-guide-36ac
[41] API Development Mastery: Building Modern Web APIs in 2025 - https://kbc.sh/blog/api-development-mastery-2025
[42] API Development Best Practices: Improve Your APIs Today - https://dotmock.com/blog/api-development-best-practices
[43] 10 Essential RESTful API Best Practices for 2025 - https://dotmock.com/blog/restful-api-best-practices
[44] 9 API Design Best Practices We Swear By (And You Should Too) - https://clouddevs.com/api-design-best-practices/
[45] A Complete Guide for 2025 - https://techpulsion.com/rest-api-best-practices/
[46] 8 Essential API Design Best Practices for 2025 - https://datanizant.com/api-design-best-practices/
[47] Top 10 REST API Design Best Practices for Scalable Web Applications - https://editorialge.com/rest-api-design-best-practices-scalable-web-apps/
[48] REST API Best Practices - https://restfulapi.net/rest-api-best-practices/
[49] REST API Design: Best Practices and Lessons Learned - https://www.kulik.io/2025/04/09/rest-api-design-best-practices-and-lessons-learned/
[50] API Design Best Practices in 2025: Trends and Techniques - https://myappapi.com/blog/api-design-best-practices-2025

## Version History

- v1.0 (2026-01-15 14:54:52): Initial version based on comprehensive research of REST API patterns and anti-patterns
