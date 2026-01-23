# Testing Quick Start Guide

**TL;DR - How to run tests right now**

## Backend Tests (Python/pytest)

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pytest
```

**What gets tested**: 41 tests covering auth endpoints, user profiles, JWT tokens, protected routes

**Common commands**:
```bash
pytest -v                    # Verbose output
pytest -x                    # Stop on first failure
pytest -k "auth"             # Run only auth tests
pytest --cov=.               # Show coverage report
```

---

## Frontend Tests (TypeScript/Jest)

```bash
cd frontend
npm test
```

**What gets tested**: API client interceptors, component rendering, form validation, age gate logic

**Common commands**:
```bash
npm run test:watch           # Re-run on file changes
npm run test:coverage        # Coverage report
npm test -- AgeGate          # Run specific test file
```

---

## Full Test Suite

```bash
# Backend
cd backend && pytest && cd ..

# Frontend
cd frontend && npm test && npm run type-check && cd ..

# Or run CI locally (requires GitHub CLI or act)
gh act -j backend-tests
gh act -j frontend-tests
```

---

## Test Files Created

### Backend
- ✅ `backend/pytest.ini` - Pytest configuration
- ✅ `backend/tests/conftest.py` - Shared fixtures
- ✅ `backend/tests/test_auth_endpoints.py` - 22 auth tests
- ✅ `backend/tests/test_users_endpoints.py` - 19 user tests

### Frontend
- ✅ `frontend/jest.config.js` - Jest configuration
- ✅ `frontend/jest.setup.js` - Global mocks
- ✅ `frontend/lib/__tests__/api.test.ts` - API client tests
- ✅ `frontend/components/__tests__/AgeGate.test.tsx` - Component tests

### CI/CD
- ✅ `.github/workflows/ci.yml` - Automated testing on push/PR

---

## What's Tested?

### Backend ✅
- User registration (duplicate emails, validation)
- User login (wrong password, missing fields)
- JWT token generation and verification
- Protected routes (401 handling)
- Token refresh
- User profile CRUD
- Review history (with pagination)
- Public vs authenticated endpoints

### Frontend ✅
- Auth token injection in API requests
- 401 error handling and redirect to login
- Age gate validation (under 21, exact age, edge cases)
- Form validation
- localStorage operations
- Component rendering and interactions

---

## CI Pipeline

Every push to `master`, `main`, or `develop` runs:
1. Backend pytest (Python 3.11)
2. Frontend Jest + TypeScript check (Node 18)
3. ESLint
4. Uploads coverage reports

**View results**: GitHub → Actions tab → Latest workflow

---

## Test Coverage Goals

| Area | Current | Goal |
|------|---------|------|
| Auth endpoints | ✅ 100% | 100% |
| User endpoints | ✅ 100% | 100% |
| API client | ✅ 85% | 90% |
| Components | ⚠️ 40% | 70% |
| Products | ❌ 0% | 80% |
| Reviews | ❌ 0% | 80% |

---

## Before Committing

```bash
# Quick pre-commit check
cd backend && pytest -x && cd ../frontend && npm test && npm run type-check
```

---

## Next Steps

1. **Add more component tests**: Login page, Profile page, UserNav
2. **Test product search**: Filters, pagination, sorting
3. **Test review submission**: Form validation, API integration
4. **Add E2E tests**: Playwright for full user journeys

---

## Need Help?

- Full documentation: [docs/TESTING.md](docs/TESTING.md)
- Backend test examples: `backend/tests/test_auth_endpoints.py`
- Frontend test examples: `frontend/components/__tests__/AgeGate.test.tsx`
- CI configuration: `.github/workflows/ci.yml`

---

**Created**: January 2026
**Status**: ✅ Production Ready
