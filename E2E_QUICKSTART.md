# E2E Testing Quick Start

**TL;DR - Run E2E tests in 3 steps**

---

## Step 1: Install Playwright Browsers (One-Time)

```bash
npx playwright install
```

Takes ~2 minutes, downloads ~500MB

---

## Step 2: Run Tests

```bash
# Interactive UI mode (RECOMMENDED for beginners)
npm run test:e2e:ui

# Or run all tests headless
npm run test:e2e

# Or watch the browser (headed mode)
npm run test:e2e:headed
```

---

## Step 3: View Results

```bash
# Open HTML report
npm run test:e2e:report
```

The report shows:
- ✅/❌ Test pass/fail status
- 📹 Videos of failures
- 📸 Screenshots
- ⏱️ Test timing

---

## What's Being Tested?

✅ **21+ E2E tests** covering:

1. **Age Gate** (4 tests)
   - Shows on first visit
   - Rejects users under 21
   - Accepts users 21+
   - Persists across pages

2. **Authentication** (6 tests)
   - Login page loads
   - Form validation
   - Protected routes
   - OAuth buttons

3. **Product Search** (5 tests)
   - Search interface
   - Filtering
   - Product details
   - Price comparison

4. **Navigation** (6 tests)
   - Home page
   - Responsive design
   - Compliance disclaimers
   - 404 handling

---

## Common Commands

```bash
# Interactive mode (pick which tests to run)
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/01-age-gate.spec.ts

# Debug mode (pause at each step)
npm run test:e2e:debug

# Run in specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Show report
npm run test:e2e:report
```

---

## Automated Testing in CI

**Every time you push code:**

1. GitHub Actions automatically runs all E2E tests
2. Tests run in Chrome, Firefox, Safari
3. Reports and videos saved as artifacts
4. You get notified if tests fail

**View results:**
- GitHub → Actions tab → Latest workflow
- Download "playwright-report" artifact

---

## Set Up Failure Notifications

### Email Alerts

1. Add GitHub secrets:
   - `EMAIL_USERNAME` = your.email@gmail.com
   - `EMAIL_PASSWORD` = Gmail app password

2. Edit `.github/workflows/test-report.yml`
   - Uncomment the `email-notification` section
   - Change `to:` email address

3. Push changes → Get emails when tests fail!

### Slack Alerts

1. Create Slack webhook → Copy URL
2. Add GitHub secret: `SLACK_WEBHOOK`
3. Uncomment `slack-notification` section in `test-report.yml`

### Discord Alerts

1. Create Discord webhook → Copy URL
2. Add GitHub secret: `DISCORD_WEBHOOK`
3. Uncomment `discord-notification` section

---

## Understanding Test Results

### ✅ Tests Passed

```
21 passed (45s)
```

All user flows work correctly!

### ❌ Tests Failed

```
✗ should navigate to login page (5.2s)
  Error: Timed out waiting for element
```

**What to do:**
1. Open report: `npm run test:e2e:report`
2. Click failed test → watch video
3. See what went wrong
4. Fix code or update test

---

## Files Created

```
playwright.config.ts              # Playwright configuration
e2e/
├── 01-age-gate.spec.ts           # Age verification tests
├── 02-authentication.spec.ts     # Login/auth tests
├── 03-product-search.spec.ts     # Product tests
├── 04-navigation.spec.ts         # Navigation tests
└── helpers.ts                     # Reusable test helpers

.github/workflows/
├── e2e-tests.yml                 # CI for E2E tests
└── test-report.yml               # Notifications
```

---

## Next Steps

1. ✅ Run tests now: `npm run test:e2e:ui`
2. ✅ Push to trigger CI
3. ✅ Set up notifications (optional)
4. ✅ Read full guide: [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)

---

## Need Help?

- **Full Guide**: [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)
- **Playwright Docs**: https://playwright.dev/
- **Interactive Tutorial**: `npm run test:e2e:ui`

**Status**: ✅ Ready to use!
