---
title:        Testing Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Testing Best Practices

## Purpose
Establish comprehensive testing strategies for ensuring code quality, reliability, and maintainability through systematic testing approaches.

## Core Testing Principles

### 1. Testing Pyramid Structure
- **Unit Tests**: Fast, isolated tests for individual functions/classes (70%)
- **Integration Tests**: Medium speed, test component interactions (20%)
- **End-to-End Tests**: Slow, test complete user scenarios (10%)
- **Rationale**: Optimize for speed and reliability while maintaining coverage

### 2. Test-Driven Development (TDD)
- **Red-Green-Refactor Cycle**: Write failing test → make it pass → refactor
- **Benefits**: Better design, fewer bugs, improved maintainability
- **Implementation**: Write tests before code to drive design decisions
- **Focus**: Test behavior and outcomes, not implementation details

### 3. Test Structure Standards
- **Setup**: Prepare test environment and data
- **Execution**: Trigger the behavior being tested
- **Validation**: Assert expected outcomes with clear messages
- **Cleanup**: Restore system to pre-test state
- **Naming**: Use descriptive names that explain test intent

## Testing Strategies

### 1. Unit Testing
- **Isolation**: Test individual components in isolation
- **Fast Execution**: Run quickly to provide immediate feedback
- **Comprehensive Coverage**: Cover edge cases and error conditions
- **Mocking**: Replace external dependencies with test doubles
- **Assertions**: Use specific, meaningful assertions

### 2. Integration Testing
- **Component Interaction**: Test how components work together
- **Database Testing**: Use test databases with proper isolation
- **API Testing**: Verify HTTP endpoints and data flow
- **External Services**: Mock third-party dependencies
- **Environment Parity**: Use production-like test environments

### 3. Mocking and Test Doubles
- **Mock**: Replace dependencies with controlled test objects
- **Stub**: Provide predetermined responses to method calls
- **Spy**: Record interactions for verification
- **Fake**: Working implementation with shortcuts for testing
- **When to Mock**: External APIs, databases, file systems, slow operations

## Test Organization

### 1. Test Structure
- **Mirror Source**: Test directory structure matches source code
- **Logical Grouping**: Group related tests in classes or modules
- **Shared Fixtures**: Reuse common test setup across tests
- **Test Categories**: Mark tests by type (unit, integration, slow)

### 2. Test Data Management
- **Factory Fixtures**: Create test data with sensible defaults
- **Parameterized Tests**: Test multiple scenarios efficiently
- **Test Builders**: Fluent interfaces for complex test data
- **Data Isolation**: Each test uses independent data

### 3. Async and Advanced Testing
- **Async Testing**: Proper handling of asynchronous code
- **Property-Based Testing**: Generate test cases automatically
- **Contract Testing**: Verify API contracts between services
- **Performance Testing**: Load and stress testing integration

## Quality Assurance

### 1. Test Quality Metrics
- **Code Coverage**: Track percentage of code exercised by tests
- **Test Execution Time**: Monitor and optimize slow tests
- **Test Reliability**: Track and fix flaky tests
- **Defect Detection Rate**: Measure test effectiveness

### 2. Continuous Testing
- **CI/CD Integration**: Run tests on every commit
- **Fast Feedback**: Prioritize fast-running tests in pipeline
- **Parallel Execution**: Run tests concurrently when possible
- **Automated Reporting**: Clear test result communication

### 3. Test Maintenance
- **Independent Tests**: Each test runs in isolation
- **Deterministic Results**: Tests are predictable and repeatable
- **Regular Cleanup**: Remove obsolete tests and update outdated ones
- **Documentation**: Document complex test scenarios and setup

## Common Anti-Patterns to Avoid

### 1. Testing Issues
- **Testing Implementation Details**: Focus on behavior, not internal structure
- **Dependent Tests**: Tests that rely on execution order
- **Slow Tests**: Avoid unnecessary delays (sleep, real network calls)
- **Flaky Tests**: Tests that pass/fail inconsistently

### 2. Test Structure Problems
- **Overly Complex Tests**: Keep tests simple and focused
- **Poor Test Names**: Use descriptive names that explain intent
- **Missing Cleanup**: Always restore system state after tests
- **Shared Mutable State**: Avoid global state between tests

### 3. Coverage Misconceptions
- **100% Coverage Goal**: Focus on meaningful coverage, not percentage
- **Testing Getters/Setters**: Don't test trivial code
- **Ignoring Edge Cases**: Test boundary conditions and error paths

## Framework-Specific Guidelines

### Python (pytest)
- Use fixtures for test setup and teardown
- Leverage parametrization for multiple test cases
- Mock external dependencies with pytest-mock
- Use TestContainers for integration tests

### JavaScript (Jest)
- Utilize snapshot testing for UI components
- Mock modules and functions appropriately
- Use async/await for asynchronous tests
- Implement proper test isolation

### Java (JUnit)
- Use dependency injection for testable code
- Implement test builders for complex objects
- Use TestContainers for database integration
- Follow AAA pattern (Arrange, Act, Assert)

## Implementation Strategy

### Phase 1: Foundation
- Establish testing pyramid structure
- Implement basic unit testing practices
- Set up CI/CD integration
- Define test naming conventions

### Phase 2: Advanced Practices
- Introduce TDD workflow
- Implement comprehensive mocking
- Add integration testing
- Establish test data management

### Phase 3: Optimization
- Optimize test execution speed
- Implement advanced testing patterns
- Add performance and contract testing
- Establish test quality metrics

### Phase 4: Continuous Improvement
- Regular test suite maintenance
- Team training on testing practices
- Tool evaluation and adoption
- Process refinement based on metrics

## Success Indicators
- Reduced bug reports in production
- Faster development cycles with confidence
- Improved code design and modularity
- Higher team productivity and morale
- Reliable automated deployment pipeline

## Version History

- v1.0 (2026-01-12): Initial version based on industry research and testing methodologies
