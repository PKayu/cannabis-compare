# E2E Testing with Playwright - Complete Guide

**For beginners: Everything you need to know about automated end-to-end testing**

---

## What is E2E Testing?

**E2E (End-to-End) testing** simulates real users clicking through your website. Instead of testing individual functions, it tests complete user journeys:

- ✅ User visits site → sees age gate → enters birth date → accesses home page
- ✅ User searches for products → clicks a result → sees product details
- ✅ User tries to access profile without login → redirected to login page

**Why it matters**: Catches bugs that unit tests miss, like:
- "The login button exists, but clicking it doesn't actually log you in"
- "Search works, but results don't display on mobile"
- "Age gate can be bypassed by refreshing"

---

## Quick Start - Run Tests Now

### 1. Install Playwright Browsers (one-time setup)

```bash
# From project root
npx playwright install
```

This downloads Chrome, Firefox, and Safari test browsers (~500MB).

### 2. Run E2E Tests Locally

```bash
# Option 1: Run all tests (headless - no browser window)
npm run test:e2e

# Option 2: See the browser while tests run (headed mode)
npm run test:e2e:headed

# Option 3: Interactive UI mode (recommended for beginners)
npm run test:e2e:ui

# Option 4: Debug mode (pause at each step)
npm run test:e2e:debug
```

### 3. View Test Results

After tests run, open the HTML report:

```bash
npm run test:e2e:report
```

This opens an interactive report showing:
- ✅ Which tests passed/failed
- 📹 Videos of failed tests
- 📸 Screenshots at failure points
- ⏱️ How long each test took

---

## What Tests Are Included?

### Test Suite Overview

| Test File | What It Tests | # of Tests |
|-----------|---------------|------------|
| `01-age-gate.spec.ts` | Age verification flow | 4 tests |
| `02-authentication.spec.ts` | Login, sign-out, protected routes | 6 tests |
| `03-product-search.spec.ts` | Product search and filtering | 5 tests |
| `04-navigation.spec.ts` | Navigation, responsive design | 6 tests |

**Total**: 21+ E2E tests covering critical user journeys

### Critical Flows Tested

1. **Age Gate Protection**
   - Shows on first visit
   - Rejects users under 21
   - Accepts users over 21
   - Persists verification across pages

2. **Authentication**
   - Login page accessible
   - Magic link form validation
   - Protected routes redirect to login
   - OAuth buttons present

3. **Product Discovery**
   - Search interface works
   - Product filtering by type
   - Product detail pages load
   - Price comparison displays

4. **Site Navigation**
   - Home page loads
   - Compliance disclaimers on all pages
   - Responsive menu (mobile/desktop)
   - 404 handling

---

## Understanding Test Reports

### When Tests Pass ✅

```
✓ e2e/01-age-gate.spec.ts:8:3 › should show age gate on first visit (1.2s)
✓ e2e/01-age-gate.spec.ts:14:3 › should reject users under 21 (2.5s)
✓ e2e/01-age-gate.spec.ts:30:3 › should accept users over 21 (1.8s)

21 passed (45s)
```

**What this means**: All user flows work correctly!

### When Tests Fail ❌

```
✗ e2e/02-authentication.spec.ts:15:3 › should navigate to login page (5.2s)

  Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
  Locator: getByRole('link', { name: /sign in/i })
  Expected: visible
  Received: <not found>
```

**What this means**:
- Test expected a "Sign In" link
- Link wasn't found on the page
- Possible causes:
  - Link text changed (e.g., "Login" instead of "Sign In")
  - Link not rendered due to bug
  - Test selector needs updating

**How to fix**:
1. Open the HTML report (`npm run test:e2e:report`)
2. Click on failed test
3. Watch the video to see what happened
4. Either fix the code or update the test

---

## How to Write New E2E Tests

### Simple Test Template

```typescript
import { test, expect } from '@playwright/test'

test('my new test', async ({ page }) => {
  // 1. Navigate to page
  await page.goto('/')

  // 2. Interact with elements
  await page.getByRole('button', { name: /click me/i }).click()

  // 3. Verify results
  await expect(page.getByText('Success!')).toBeVisible()
})
```

### Common Playwright Commands

```typescript
// Navigate
await page.goto('/products')

// Find elements (prefer accessible selectors)
page.getByRole('button', { name: /submit/i })  // Find button by text
page.getByLabel('Email')                        // Find input by label
page.getByPlaceholder('Search...')             // Find by placeholder
page.getByText('Welcome')                       // Find by text content

// Interactions
await button.click()                            // Click
await input.fill('value')                       // Type text
await checkbox.check()                          // Check checkbox
await dropdown.selectOption('option')           // Select from dropdown

// Assertions
await expect(element).toBeVisible()             // Element shows on page
await expect(element).toHaveText('text')        // Element has specific text
await expect(page).toHaveURL(/\/login/)        // URL matches pattern
```

### Test Organization Tips

1. **Group related tests**:
   ```typescript
   test.describe('User Profile', () => {
     test('should load profile page', async ({ page }) => { ... })
     test('should update username', async ({ page }) => { ... })
   })
   ```

2. **Use beforeEach for setup**:
   ```typescript
   test.beforeEach(async ({ page }) => {
     // This runs before each test
     await bypassAgeGate(page)
   })
   ```

3. **Use helpers** (see `e2e/helpers.ts`):
   ```typescript
   import { bypassAgeGate, mockAuthentication } from './helpers'

   test('my test', async ({ page }) => {
     await bypassAgeGate(page)
     await mockAuthentication(page)
     // Now test as an authenticated user
   })
   ```

---

## Automated Testing & Reports in CI

### How It Works

1. **Push code** to GitHub
2. **GitHub Actions automatically**:
   - Starts backend server
   - Starts frontend server
   - Runs all E2E tests in Chrome, Firefox, Safari
   - Generates reports
   - Saves videos of failures
3. **You get notified** if tests fail

### Viewing CI Test Results

**Option 1: GitHub Actions Tab**
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Click on latest workflow run
4. See status: ✅ passed or ❌ failed

**Option 2: Check PR Comments**
- On pull requests, bot comments with test results
- Includes link to full report

**Option 3: Download Artifacts**
1. Go to workflow run
2. Scroll to bottom → "Artifacts" section
3. Download `playwright-report`
4. Extract zip and open `index.html`

---

## Setting Up Notifications

### Get Alerts When Tests Fail

The `test-report.yml` workflow is ready for notifications. Here's how to activate them:

#### Option 1: Email Notifications

1. **Get Gmail App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Create password for "GitHub Actions"

2. **Add GitHub Secrets**:
   - Go to repo → Settings → Secrets → Actions
   - Add `EMAIL_USERNAME` = your.email@gmail.com
   - Add `EMAIL_PASSWORD` = app password

3. **Uncomment email section in `.github/workflows/test-report.yml`**:
   ```yaml
   email-notification:
     runs-on: ubuntu-latest
     if: ${{ github.event.workflow_run.conclusion == 'failure' }}
     steps:
       - name: Send email
         uses: dawidd6/action-send-mail@v3
         with:
           server_address: smtp.gmail.com
           server_port: 465
           username: ${{ secrets.EMAIL_USERNAME }}
           password: ${{ secrets.EMAIL_PASSWORD }}
           subject: "❌ Test Failure: ${{ github.event.workflow_run.name }}"
           to: your.email@gmail.com  # Change this to your email
           from: GitHub Actions
           body: |
             Test workflow failed!

             Workflow: ${{ github.event.workflow_run.name }}
             Branch: ${{ github.event.workflow_run.head_branch }}

             View: ${{ github.event.workflow_run.html_url }}
   ```

Now you'll get an email whenever tests fail!

#### Option 2: Slack Notifications

1. **Create Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create app → Incoming Webhooks → Add to workspace
   - Copy webhook URL

2. **Add GitHub Secret**:
   - Repo → Settings → Secrets → Actions
   - Add `SLACK_WEBHOOK` = your webhook URL

3. **Uncomment Slack section in `.github/workflows/test-report.yml`**:
   ```yaml
   slack-notification:
     runs-on: ubuntu-latest
     if: ${{ github.event.workflow_run.conclusion == 'failure' }}
     steps:
       - name: Send Slack notification
         uses: 8398a7/action-slack@v3
         with:
           status: ${{ github.event.workflow_run.conclusion }}
           text: |
             Test Failed: ${{ github.event.workflow_run.name }}
             Branch: ${{ github.event.workflow_run.head_branch }}
             View: ${{ github.event.workflow_run.html_url }}
           webhook_url: ${{ secrets.SLACK_WEBHOOK }}
   ```

#### Option 3: Discord Notifications

1. **Create Discord Webhook**:
   - Discord server → Edit channel → Integrations → Webhooks
   - Copy webhook URL

2. **Add to workflow**:
   ```yaml
   discord-notification:
     runs-on: ubuntu-latest
     if: ${{ github.event.workflow_run.conclusion == 'failure' }}
     steps:
       - uses: sarisia/actions-status-discord@v1
         with:
           webhook: ${{ secrets.DISCORD_WEBHOOK }}
           title: "Test Failed"
           description: "E2E tests failed on ${{ github.event.workflow_run.head_branch }}"
   ```

---

## Common Issues & Solutions

### Issue: "All tests skipped"

**Cause**: Frontend/backend servers not running

**Solution**:
```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run tests
npm run test:e2e
```

### Issue: "Timeout waiting for page"

**Cause**: Server not ready or wrong URL

**Solution**: Check `playwright.config.ts` has correct `baseURL`:
```typescript
use: {
  baseURL: 'http://localhost:3000',  // Make sure this is correct
}
```

### Issue: "Element not found"

**Cause**: Page changed or element selector wrong

**Solution**:
1. Run test in headed mode to see page: `npm run test:e2e:headed`
2. Check what's actually on the page
3. Update test selector or fix the page

### Issue: "Tests fail in CI but pass locally"

**Cause**: Timing issues or missing data

**Solutions**:
- Add `await page.waitForTimeout(1000)` for loading states
- Use `await page.waitForLoadState('networkidle')`
- Check CI has same environment variables

### Issue: "Browsers not installed"

**Solution**:
```bash
npx playwright install
```

---

## Test Development Workflow

### Daily Development

```bash
# 1. Make code changes
# 2. Run affected tests
npm run test:e2e:ui  # Interactive mode to select tests

# 3. If tests fail, debug
npm run test:e2e:debug

# 4. Once passing, run full suite
npm run test:e2e

# 5. Commit and push (CI runs automatically)
```

### Adding New Features

1. **Write test first** (TDD approach):
   ```bash
   # Create new test file
   touch e2e/05-my-feature.spec.ts
   ```

2. **Run test** (should fail):
   ```bash
   npm run test:e2e:ui  # Select your new test
   ```

3. **Implement feature** until test passes

4. **Commit** with passing tests

---

## Best Practices

### ✅ Do

- Use descriptive test names: `test('should show error for invalid email')`
- Test happy path AND error cases
- Use accessible selectors: `getByRole`, `getByLabel`
- Add `await` before all async operations
- Group related tests with `test.describe()`
- Keep tests independent (don't rely on test order)

### ❌ Don't

- Use CSS selectors like `.btn-primary` (brittle)
- Make tests depend on each other
- Test implementation details
- Forget to clean up (clear localStorage, cookies)
- Test third-party libraries (trust they work)
- Write 500-line tests (break into smaller tests)

---

## Understanding Test Files

### Test Structure

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  // Runs before each test in this group
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('specific behavior', async ({ page }) => {
    // Arrange - set up test conditions
    await page.getByLabel('Email').fill('test@example.com')

    // Act - perform action
    await page.getByRole('button', { name: /submit/i }).click()

    // Assert - verify result
    await expect(page.getByText('Success')).toBeVisible()
  })
})
```

### Helper Functions

Located in `e2e/helpers.ts`:

```typescript
// Skip age gate for most tests
await bypassAgeGate(page)

// Complete full age verification flow
await completeAgeGate(page)

// Mock user authentication
await mockAuthentication(page, { email: 'test@example.com' })

// Wait for specific API call
await waitForAPIResponse(page, '/api/products', 200)

// Take debugging screenshot
await takeDebugScreenshot(page, 'checkout-page')
```

---

## Performance Tips

### Speed Up Tests

```typescript
// Run tests in parallel
npx playwright test --workers=4

// Run only specific browser
npx playwright test --project=chromium

// Run specific file
npx playwright test e2e/01-age-gate.spec.ts

// Skip slow tests in development
test.skip('slow test', async ({ page }) => { ... })
```

### Reduce Flakiness

```typescript
// Wait for element to be visible AND stable
await expect(element).toBeVisible()

// Wait for network to be idle
await page.waitForLoadState('networkidle')

// Increase timeout for slow operations
await expect(element).toBeVisible({ timeout: 10000 })

// Retry flaky assertions
test.describe.configure({ retries: 2 })
```

---

## Next Steps

1. ✅ **Run tests locally** to see them work
2. ✅ **Push code** to trigger CI
3. ✅ **Set up notifications** (email/Slack/Discord)
4. ✅ **Add tests** for new features as you build
5. ✅ **Review reports** when tests fail

---

## Resources

- **Playwright Docs**: https://playwright.dev/
- **Test Examples**: See `e2e/*.spec.ts` files
- **Helper Functions**: `e2e/helpers.ts`
- **CI Configuration**: `.github/workflows/e2e-tests.yml`
- **Interactive Mode**: `npm run test:e2e:ui` ← Best for learning!

---

## Questions?

**"How do I know what to test?"**
→ Test what users do: click buttons, fill forms, navigate pages

**"Tests are slow, is this normal?"**
→ E2E tests are slower than unit tests. Run in parallel to speed up.

**"Should I test every single page?"**
→ Focus on critical flows. You have 21 tests now covering the most important paths.

**"Test failed but my code works locally?"**
→ Check CI environment variables, timing issues, or data differences

---

**Created**: January 2026
**Status**: ✅ Ready to Use
**Support**: Check docs or open an issue
