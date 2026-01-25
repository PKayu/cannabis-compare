# Testing Guide

**Utah Cannabis Aggregator - Complete Testing Documentation**

This is the single source of truth for all testing: unit tests, integration tests, E2E tests, and CI/CD.

---

## Quick Start

### Run All Tests

```bash
# Use the test script (recommended)
scripts\run-tests.bat

# Or manually:
cd backend && pytest && cd ../frontend && npm test
```

### Run E2E Tests

```bash
cd frontend

# Interactive UI mode (BEST for beginners)
npm run test:e2e:ui

# Run all tests headless
npm run test:e2e

# View results
npm run test:e2e:report
```

---

## Table of Contents

1. [Overview](#overview)
2. [Backend Testing (pytest)](#backend-testing)
3. [Frontend Testing (Jest)](#frontend-testing)
4. [E2E Testing (Playwright)](#e2e-testing)
5. [Test Reports](#test-reports)
6. [Continuous Integration](#continuous-integration)
7. [Writing New Tests](#writing-new-tests)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The project uses a comprehensive testing strategy covering:

- **Backend**: pytest for API endpoints, business logic, and database operations
- **Frontend**: Jest + React Testing Library for components and client-side logic
- **CI/CD**: GitHub Actions for automated testing on every commit

### Test Coverage Summary

| Test Type | Framework | # Tests | What's Tested |
|-----------|-----------|---------|---------------|
| Backend | pytest | 74+ | Auth, users, APIs, JWT tokens |
| Frontend | Jest | 20+ | Components, API client, forms |
| E2E | Playwright | 21+ | Full user journeys |

### Testing Philosophy

**What We Test:**
- Critical user flows: authentication, profile access, data submission
- Security: token validation, protected routes, authorization
- Business logic: age verification, data normalization, search

**What We Don't Test:**
- Third-party libraries (axios, React, FastAPI)
- Framework internals (Next.js routing, SQLAlchemy)
- Styling (CSS/Tailwind classes)

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

## E2E Testing

E2E (End-to-End) testing simulates real users clicking through your website, testing complete user journeys.

### Setup (One Time)

```bash
cd frontend
npx playwright install  # Downloads ~500MB of browsers
```

### Quick Commands

```bash
cd frontend

# Interactive UI mode (BEST for beginners)
npm run test:e2e:ui

# Run all tests headless
npm run test:e2e

# Watch browser while tests run
npm run test:e2e:headed

# Debug mode (pause at each step)
npm run test:e2e:debug

# View HTML report
npm run test:e2e:report

# Run specific test file
npx playwright test e2e/01-age-gate.spec.ts

# Run in specific browser
npx playwright test --project=chromium
```

### Test Suite Overview

| Test File | What It Tests | # Tests |
|-----------|---------------|---------|
| `01-age-gate.spec.ts` | Age verification flow | 4 |
| `02-authentication.spec.ts` | Login, sign-out, protected routes | 6 |
| `03-product-search.spec.ts` | Product search and filtering | 5 |
| `04-navigation.spec.ts` | Navigation, responsive design | 6 |

**Total**: 21+ E2E tests covering critical user journeys

### E2E Test Structure

```
frontend/
├── e2e/
│   ├── 01-age-gate.spec.ts       # Age verification tests
│   ├── 02-authentication.spec.ts # Login/auth tests
│   ├── 03-product-search.spec.ts # Product tests
│   ├── 04-navigation.spec.ts     # Navigation tests
│   └── helpers.ts                # Reusable test helpers
└── playwright.config.ts          # Playwright configuration
```

### Writing E2E Tests

```typescript
import { test, expect } from '@playwright/test'

test('should show age gate on first visit', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /I am 21/i }).click()
  await expect(page.getByText('Welcome')).toBeVisible()
})
```

### Helper Functions

```typescript
import { bypassAgeGate, mockAuthentication } from './helpers'

test('my test', async ({ page }) => {
  await bypassAgeGate(page)
  await mockAuthentication(page)
  // Now test as authenticated user
})
```

---

## Test Reports

### HTML Reports (E2E)

```bash
npm run test:e2e
npm run test:e2e:report
```

**Report includes:**
- ✅/❌ Test pass/fail status
- 📹 Videos of failures
- 📸 Screenshots at failure points
- ⏱️ Test timing

### Coverage Reports

**Backend:**
```bash
cd backend
pytest --cov=. --cov-report=html
start htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm run test:coverage
start coverage/lcov-report/index.html
```

### Coverage Goals

| Area | Current | Goal |
|------|---------|------|
| Auth endpoints | ✅ 100% | 100% |
| User endpoints | ✅ 100% | 100% |
| API client | ✅ 85% | 90% |
| Components | ⚠️ 40% | 70% |

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

### E2E Tests Failing

**Issue**: "All tests skipped"
Servers not running. Start backend and frontend first:
```bash
scripts\start-backend.bat  # Terminal 1
scripts\start-frontend.bat  # Terminal 2
npm run test:e2e  # Terminal 3
```

**Issue**: "Timeout waiting for page"
Check `playwright.config.ts` has correct `baseURL: 'http://localhost:3000'`

**Issue**: "Element not found"
Run in headed mode to see what's on page:
```bash
npm run test:e2e:headed
```

**Issue**: "Tests pass locally but fail in CI"
Add `await page.waitForLoadState('networkidle')` for timing issues

---

## Setting Up Failure Notifications

### Email Notifications

1. Get Gmail App Password (Google Account → Security → App Passwords)
2. Add GitHub Secrets: `EMAIL_USERNAME` and `EMAIL_PASSWORD`
3. Uncomment email section in `.github/workflows/test-report.yml`

### Slack/Discord

See `test-report.yml` for webhook setup instructions.

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Jest documentation](https://jestjs.io/docs/getting-started)
- [Playwright documentation](https://playwright.dev/)
- [Testing Library docs](https://testing-library.com/react)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Last Updated**: January 2026
**Status**: ✅ Production Ready
