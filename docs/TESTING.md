# Testing Strategy & Guide

**Utah Cannabis Aggregator - Automated Testing**

This document covers the testing infrastructure, strategies, and guidelines for the Utah Cannabis Aggregator project.

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Backend Testing (Python/pytest)](#backend-testing)
4. [Frontend Testing (TypeScript/Jest)](#frontend-testing)
5. [Continuous Integration](#continuous-integration)
6. [Running Tests Locally](#running-tests-locally)
7. [Writing New Tests](#writing-new-tests)
8. [Test Coverage](#test-coverage)

---

## Overview

The project uses a comprehensive testing strategy covering:

- **Backend**: pytest for API endpoints, business logic, and database operations
- **Frontend**: Jest + React Testing Library for components and client-side logic
- **CI/CD**: GitHub Actions for automated testing on every commit

### Current Test Coverage

**Backend**:
- ✅ 41 tests covering authentication and user endpoints
- ✅ JWT token generation and verification
- ✅ Protected route middleware
- ✅ Database operations with in-memory SQLite

**Frontend**:
- ✅ API client interceptors (auth tokens, error handling)
- ✅ Component rendering and user interactions
- ✅ Form validation and age verification logic

---

## Testing Philosophy

### What We Test

1. **Critical User Flows**: Authentication, profile access, data submission
2. **Security**: Token validation, protected routes, authorization
3. **Business Logic**: Age verification, data normalization, search algorithms
4. **API Contracts**: Request/response structures, error handling

### What We Don't Test

1. **Third-party libraries**: We trust axios, React, FastAPI, etc.
2. **Framework internals**: Next.js routing, SQLAlchemy internals
3. **Styling**: CSS/Tailwind classes (visual regression testing can be added later)
4. **External services**: Supabase API (we mock these)

### Test Pyramid

```
       /\
      /  \     E2E (Future - Playwright)
     /____\
    /      \   Integration Tests (API endpoints, component interactions)
   /________\
  /__________\ Unit Tests (Functions, utilities, business logic)
```

We focus on integration and unit tests for fast, reliable feedback.

---

## Backend Testing

### Technology Stack

- **Framework**: pytest 7.4.3
- **Async Support**: pytest-asyncio
- **Test Client**: FastAPI TestClient
- **Database**: In-memory SQLite (for isolation)
- **Fixtures**: Defined in `tests/conftest.py`

### Directory Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── test_auth_endpoints.py   # Auth endpoint tests
│   ├── test_users_endpoints.py  # User profile tests
│   ├── test_matcher.py          # Product matching logic
│   └── test_scraper.py          # Web scraper tests
├── pytest.ini                   # Pytest configuration
└── requirements.txt             # Includes pytest dependencies
```

### Running Backend Tests

```bash
# From project root
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_endpoints.py

# Run specific test class
pytest tests/test_auth_endpoints.py::TestRegistration

# Run specific test function
pytest tests/test_auth_endpoints.py::TestRegistration::test_register_new_user_success

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run only tests marked as 'auth'
pytest -m auth

# Run tests and stop on first failure
pytest -x
```

### Key Fixtures

**`db_session`**: Provides a fresh in-memory database for each test
```python
def test_create_user(db_session):
    user = User(email="test@example.com", username="test")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
```

**`client`**: FastAPI test client with database dependency override
```python
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

**`authenticated_user`**: Pre-created user with valid JWT token
```python
def test_protected_route(client, auth_headers):
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
```

### Test Organization

Tests are organized by router/feature:
- `test_auth_endpoints.py` - Registration, login, token management
- `test_users_endpoints.py` - Profile CRUD, review history
- Future: `test_products.py`, `test_reviews.py`, `test_dispensaries.py`

Each test file uses test classes to group related tests:
```python
class TestRegistration:
    """Tests for /api/auth/register endpoint"""

    def test_register_new_user_success(self, client, test_user_data):
        ...

    def test_register_duplicate_email(self, client, create_test_user):
        ...
```

### Mocking External Services

Supabase is mocked in `conftest.py` to avoid real API calls:
```python
class MockSupabaseClient:
    @staticmethod
    def create_user(email: str, password: str):
        return {"id": str(uuid.uuid4()), "email": email}
```

This ensures tests:
- Run without network dependencies
- Execute quickly
- Don't require Supabase credentials

---

## Frontend Testing

### Technology Stack

- **Framework**: Jest 30.x
- **Testing Library**: @testing-library/react 16.x
- **User Interactions**: @testing-library/user-event
- **Mocking**: axios-mock-adapter, jest mocks
- **Environment**: jsdom (simulates browser)

### Directory Structure

```
frontend/
├── __tests__/               # Top-level integration tests (optional)
├── components/
│   ├── AgeGate.tsx
│   └── __tests__/
│       └── AgeGate.test.tsx
├── lib/
│   ├── api.ts
│   └── __tests__/
│       └── api.test.ts
├── app/
│   └── (tests can go here too)
├── jest.config.js           # Jest configuration
└── jest.setup.js            # Global test setup
```

### Running Frontend Tests

```bash
# From project root
cd frontend

# Run all tests
npm test

# Run in watch mode (re-runs on file changes)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- AgeGate.test.tsx

# Run tests matching pattern
npm test -- api

# Update snapshots (if using snapshot tests)
npm test -- -u
```

### Writing Component Tests

Example test structure:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('should handle user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)

    const button = screen.getByRole('button')
    await user.click(button)

    expect(screen.getByText('Clicked!')).toBeInTheDocument()
  })
})
```

### Testing Patterns

**Testing Forms**:
```typescript
const user = userEvent.setup()
const input = screen.getByLabelText('Email')
await user.type(input, 'test@example.com')
await user.click(screen.getByRole('button', { name: /submit/i }))
```

**Testing Async Operations**:
```typescript
await waitFor(() => {
  expect(screen.getByText('Data loaded')).toBeInTheDocument()
})
```

**Mocking API Calls**:
```typescript
import MockAdapter from 'axios-mock-adapter'
import { apiClient } from '@/lib/api'

const mock = new MockAdapter(apiClient)
mock.onGet('/api/products').reply(200, { products: [] })
```

### Mocked Modules

**Next.js Router**: Automatically mocked in `jest.setup.js`
```typescript
const mockPush = jest.fn()
// useRouter() returns mocked push, replace, etc.
```

**Supabase**: Mocked to return empty sessions by default
```typescript
createClientComponentClient().auth.getSession() // Returns null session
```

You can override mocks in specific tests:
```typescript
jest.mock('@supabase/auth-helpers-nextjs', () => ({
  createClientComponentClient: jest.fn(() => ({
    auth: {
      getSession: jest.fn(() => Promise.resolve({
        data: { session: { access_token: 'test-token' } }
      }))
    }
  }))
}))
```

---

## Continuous Integration

### GitHub Actions Workflow

Located at `.github/workflows/ci.yml`, runs on:
- Push to `master`, `main`, or `develop` branches
- Pull requests to these branches

### Jobs

1. **backend-tests**: Runs pytest on Python 3.11
2. **frontend-tests**: Runs Jest and type-check on Node 18
3. **lint**: Runs ESLint on frontend code
4. **test-summary**: Aggregates results and fails if any job fails

### Viewing CI Results

1. Go to GitHub repository → Actions tab
2. Click on latest workflow run
3. View job logs for failures

CI must pass before merging pull requests.

---

## Running Tests Locally

### First-Time Setup

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

### Pre-Commit Testing

Before committing code:
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run type-check
npm test
npm run lint
```

### Quick Test Commands

Create these aliases for convenience:
```bash
# Backend tests
alias be-test="cd backend && pytest -v"

# Frontend tests
alias fe-test="cd frontend && npm test"

# All tests
alias test-all="be-test && fe-test"
```

---

## Writing New Tests

### Backend Test Template

```python
"""
Test suite for [feature name]
"""
import pytest
from fastapi import status


@pytest.mark.integration  # Or @pytest.mark.unit
class TestFeatureName:
    """Tests for [endpoint/feature]"""

    def test_success_case(self, client, authenticated_user, auth_headers):
        """Test successful operation"""
        response = client.get("/api/endpoint", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "expected_value"

    def test_error_case(self, client):
        """Test error handling"""
        response = client.get("/api/endpoint")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### Frontend Test Template

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('should render with default props', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('should handle user interaction', async () => {
    const user = userEvent.setup()
    const mockCallback = jest.fn()

    render(<MyComponent onSubmit={mockCallback} />)

    await user.click(screen.getByRole('button'))
    expect(mockCallback).toHaveBeenCalled()
  })
})
```

### Test Naming Conventions

- **Backend**: `test_[feature]_[scenario].py`
- **Frontend**: `[Component].test.tsx`
- **Test functions**: `test_should_[expected_behavior]`
- **Test classes**: `Test[FeatureName]`

### Assertions Best Practices

**Backend**:
```python
# ✅ Good - specific assertions
assert response.status_code == 200
assert "email" in response.json()
assert response.json()["email"] == "test@example.com"

# ❌ Bad - vague assertions
assert response.status_code != 404
assert len(response.json()) > 0
```

**Frontend**:
```typescript
// ✅ Good - accessible queries
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText('Email address')

// ❌ Bad - brittle queries
screen.getByTestId('submit-btn')  // Use only when necessary
screen.getByClassName('btn-primary')
```

---

## Test Coverage

### Viewing Coverage Reports

**Backend**:
```bash
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html  # Or start htmlcov/index.html on Windows
```

**Frontend**:
```bash
cd frontend
npm run test:coverage
open coverage/lcov-report/index.html
```

### Coverage Goals

- **Critical paths**: 90%+ (auth, payments, data submission)
- **Business logic**: 80%+ (product matching, search, normalization)
- **UI components**: 70%+ (forms, interactive elements)
- **Utilities**: 80%+ (helpers, formatters, validators)

### What Coverage Doesn't Tell You

Coverage shows **lines executed**, not **quality of tests**. Focus on:
- Testing edge cases
- Verifying error handling
- Testing user workflows end-to-end
- Validating security boundaries

---

## Troubleshooting

### Backend Tests Failing

**Issue**: `ImportError: No module named 'pytest'`
**Solution**: Activate virtual environment
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**Issue**: `Database connection failed`
**Solution**: Tests use in-memory SQLite, no real database needed. Check `conftest.py` fixtures.

**Issue**: `ValueError: password cannot be longer than 72 bytes`
**Solution**: Ensure `bcrypt>=4.0.0,<5.0.0` in requirements.txt (known compatibility issue)

### Frontend Tests Failing

**Issue**: `Cannot find module 'next/navigation'`
**Solution**: Ensure mocks in `jest.setup.js` are correct

**Issue**: `ReferenceError: localStorage is not defined`
**Solution**: jsdom should provide localStorage. Check jest.config.js has `testEnvironment: 'jsdom'`

**Issue**: `Warning: useRouter only works in Client Components`
**Solution**: Add `'use client'` directive or mock Next.js router properly

### CI Failing

**Issue**: Tests pass locally but fail in CI
**Solution**: Check environment variables, ensure no local-only dependencies

**Issue**: CI times out
**Solution**: Tests should complete in <5 minutes. Optimize slow tests or increase timeout.

---

## Next Steps

### Recommended Additions

1. **E2E Testing**: Add Playwright for full user journey tests
2. **Performance Testing**: Add load tests for API endpoints
3. **Visual Regression**: Add screenshot comparison for UI
4. **Mutation Testing**: Verify test quality with mutation coverage

### Test Expansion Priorities

1. **Products Router**: Search, filtering, product details
2. **Reviews System**: CRUD operations, validation, moderation
3. **Scrapers**: Data ingestion, normalization, deduplication
4. **Admin Functions**: User management, data cleanup

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Testing Library docs](https://testing-library.com/react)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Next.js testing guide](https://nextjs.org/docs/app/building-your-application/testing)
- [Jest documentation](https://jestjs.io/docs/getting-started)

---

**Last Updated**: January 2026
**Maintained By**: Development Team
**Questions?**: Open an issue or check project documentation
