# How to Get Automated Test Reports

**Simple guide to automated testing and getting notified when things break**

---

## What You Have Now

### ✅ Automated Testing Setup
- **Backend**: 74 tests (authentication, user profiles, APIs)
- **Frontend**: Component and API tests
- **E2E**: 21+ full user journey tests
- **CI/CD**: Tests run automatically on every push

### ✅ Automated Reports
- **HTML Reports**: Beautiful visual reports with videos
- **Test Summaries**: Automatic comments on PRs
- **Failure Notifications**: Email/Slack/Discord alerts

---

## Getting Reports - 3 Ways

### Method 1: Local Testing (Your Computer)

**Run tests and see results immediately:**

```bash
# E2E Tests (RECOMMENDED - most visual)
npm run test:e2e:ui        # Interactive - pick which tests to run
npm run test:e2e:report    # View last test results

# Backend Tests
cd backend
pytest -v                  # See all test results

# Frontend Tests
cd frontend
npm test                   # Run unit tests
```

**What you see:**
- ✅ Green checkmarks = tests passed
- ❌ Red X = tests failed
- 📹 Videos of what happened
- 📸 Screenshots at failure points

---

### Method 2: GitHub Actions (Automatic)

**Tests run automatically when you push code:**

1. **Make code changes**
2. **Commit and push**:
   ```bash
   git add .
   git commit -m "your changes"
   git push
   ```

3. **View results**:
   - Go to GitHub.com → Your Repository
   - Click "Actions" tab
   - Click latest workflow run
   - See if tests passed or failed

**What you see:**
- ✅ Green dot = all tests passed
- ❌ Red X = some tests failed
- Click workflow → See which tests failed
- Download artifacts → Get full reports

---

### Method 3: Pull Request Comments (Automatic)

**Bot comments on PRs with test results:**

When you create a pull request:
1. GitHub Actions runs all tests
2. Bot posts comment with results:

```markdown
## 🎭 E2E Test Results

✅ All E2E tests passed!

- Age Gate: 4/4 ✅
- Authentication: 6/6 ✅
- Product Search: 5/5 ✅
- Navigation: 6/6 ✅

[View full report](link to artifacts)
```

If tests fail, the comment shows which ones failed.

---

## Getting Notified When Tests Fail

### Option 1: Email Notifications (Easiest)

**Setup once, get emails forever:**

1. **Get Gmail App Password** (2 minutes):
   ```
   1. Go to myaccount.google.com
   2. Security → 2-Step Verification
   3. Scroll down → App Passwords
   4. Create password for "GitHub Actions"
   5. Copy the 16-character password
   ```

2. **Add to GitHub** (1 minute):
   ```
   1. Your Repo → Settings
   2. Secrets and variables → Actions
   3. New secret:
      Name: EMAIL_USERNAME
      Value: your.email@gmail.com

   4. New secret:
      Name: EMAIL_PASSWORD
      Value: [paste the 16-character password]
   ```

3. **Enable notifications** (1 minute):
   ```
   1. Open file: .github/workflows/test-report.yml
   2. Find line 50: # email-notification:
   3. Delete the # from all lines in that section (lines 50-70)
   4. Change "to: your.email@gmail.com" to YOUR email
   5. Save and commit the file
   ```

4. **Test it**:
   ```bash
   # Push a change
   git add .
   git commit -m "test notification"
   git push

   # If any test fails, you'll get an email!
   ```

**Email you'll receive:**
```
Subject: ❌ Test Failure: E2E Tests

Test workflow failed!

Workflow: E2E Tests
Branch: main
Triggered by: YourUsername

View the full workflow run:
[link to GitHub Actions]
```

---

### Option 2: Slack Notifications

**Setup once, get Slack messages when tests fail:**

1. **Create Slack Webhook**:
   ```
   1. Go to api.slack.com/apps
   2. Create New App → From scratch
   3. Name: "Test Notifications", pick workspace
   4. Incoming Webhooks → Activate
   5. Add New Webhook to Workspace
   6. Pick channel (e.g., #dev-alerts)
   7. Copy Webhook URL
   ```

2. **Add to GitHub**:
   ```
   Repo → Settings → Secrets → Actions
   New secret:
   Name: SLACK_WEBHOOK
   Value: [paste webhook URL]
   ```

3. **Enable in workflow**:
   ```
   Edit .github/workflows/test-report.yml
   Uncomment the slack-notification section (lines ~40-50)
   ```

**Slack message you'll get:**
```
❌ Test Failed: E2E Tests
Branch: main
View: [link]
```

---

### Option 3: Discord Notifications

**Setup once, get Discord pings:**

1. **Create Discord Webhook**:
   ```
   1. Discord Server → Channel settings
   2. Integrations → Webhooks → New Webhook
   3. Name: "Test Notifications"
   4. Copy Webhook URL
   ```

2. **Add to GitHub**:
   ```
   New secret:
   Name: DISCORD_WEBHOOK
   Value: [webhook URL]
   ```

3. **Enable in workflow**:
   ```
   Uncomment discord-notification in test-report.yml
   ```

---

## Understanding Test Reports

### HTML Report (Playwright E2E)

**Most detailed report with videos:**

```bash
# Run tests
npm run test:e2e

# Open report
npm run test:e2e:report
```

**What's inside:**
- **Timeline**: Visual timeline of test execution
- **Videos**: Watch what happened during test (only for failures)
- **Screenshots**: See exact moment of failure
- **Traces**: Step-by-step replay of user actions
- **Errors**: Full error messages with stack traces

**Example:**
```
Age Gate Tests
├── ✅ should show age gate on first visit (1.2s)
├── ✅ should reject users under 21 (2.5s)
├── ❌ should accept users over 21 (5.0s)
│   └── 📹 Video: test-results/video.webm
│   └── 📸 Screenshot: test-results/screenshot.png
│   └── ❌ Error: Element not found: button[Continue]
```

Click the ❌ to see video and screenshots.

---

### Backend Coverage Report

**See which code is tested:**

```bash
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html  # Or "start htmlcov/index.html" on Windows
```

**What you see:**
- **Green lines**: Tested code ✅
- **Red lines**: NOT tested code ❌
- **Yellow lines**: Partially tested code ⚠️
- **Percentages**: How much of each file is tested

---

### Frontend Coverage Report

**See React component test coverage:**

```bash
cd frontend
npm run test:coverage
open coverage/lcov-report/index.html
```

Shows same info as backend but for frontend code.

---

## Downloading Reports from CI

**When tests run in CI, reports are saved:**

1. **Go to GitHub Actions**:
   ```
   Your Repo → Actions → Click latest workflow
   ```

2. **Scroll to bottom**:
   ```
   Artifacts section:
   - playwright-report (E2E test results)
   - backend-test-results (pytest results)
   - frontend-coverage (Jest coverage)
   ```

3. **Download and unzip**:
   ```
   Click "playwright-report" → Downloads zip file
   Unzip it
   Open index.html in browser
   ```

**Reports are kept for 30 days**

---

## What Tests Are Running?

### Every Push Triggers:

1. **Backend Tests** (74 tests, ~10 seconds)
   - User registration/login
   - JWT token handling
   - Protected routes
   - Profile CRUD
   - API validation

2. **Frontend Tests** (~5 seconds)
   - Component rendering
   - API client
   - Form validation
   - User interactions

3. **E2E Tests** (21+ tests, ~60 seconds)
   - Full user journeys
   - Age gate flow
   - Authentication flow
   - Product search
   - Navigation
   - Multi-browser (Chrome, Firefox, Safari, Mobile)

**Total time**: ~75 seconds for complete test suite

---

## Common Scenarios

### Scenario 1: "I want to run tests before pushing"

```bash
# Quick check
cd backend && pytest -x       # Stop on first failure
cd frontend && npm test
npm run test:e2e

# If all pass, push:
git push
```

---

### Scenario 2: "Tests failed in CI, how do I see what broke?"

```bash
# Option 1: Check GitHub
1. Go to Actions → Failed workflow
2. Click failed job
3. Read error messages
4. Download artifacts for full report

# Option 2: Run locally
npm run test:e2e:ui    # Run same tests interactively
npm run test:e2e:report  # See HTML report
```

---

### Scenario 3: "I want to debug a specific failing test"

```bash
# Run in debug mode (pauses at each step)
npm run test:e2e:debug

# Or run specific test file
npx playwright test e2e/01-age-gate.spec.ts --debug

# Or use UI mode
npm run test:e2e:ui  # Select the failing test
```

---

### Scenario 4: "I need to show test results to team"

```bash
# Generate report
npm run test:e2e

# Open report
npm run test:e2e:report

# Share the URL or export:
# Report is at: playwright-report/index.html
# Zip the folder and share
```

---

## Troubleshooting

### "No notifications received"

**Check:**
1. Secrets are added correctly in GitHub
2. Email/webhook URLs are correct
3. Notification code is uncommented in `test-report.yml`
4. Tests actually failed (notifications only on failure)
5. Check spam folder for emails

---

### "Can't open HTML report"

**Solution:**
```bash
# Make sure tests ran first
npm run test:e2e

# Then open report
npm run test:e2e:report

# Or manually:
open playwright-report/index.html
```

---

### "Tests pass locally but fail in CI"

**Common causes:**
1. **Environment variables** - CI might not have all secrets set
2. **Timing issues** - CI is slower, need longer timeouts
3. **Data differences** - Different database state

**Debug:**
```bash
# Download CI artifacts
# Run tests with same environment as CI
# Add more wait times in tests
```

---

## Quick Reference Commands

```bash
# E2E Testing
npm run test:e2e                # Run all E2E tests
npm run test:e2e:ui             # Interactive mode
npm run test:e2e:headed         # Watch browser
npm run test:e2e:debug          # Debug mode
npm run test:e2e:report         # View report

# Backend Testing
cd backend
pytest                          # Run all tests
pytest -v                       # Verbose
pytest -x                       # Stop on first failure
pytest --cov=.                  # With coverage

# Frontend Testing
cd frontend
npm test                        # Run tests
npm run test:watch              # Watch mode
npm run test:coverage           # With coverage
```

---

## Next Steps

1. ✅ **Run tests locally** to see them work
2. ✅ **Push code** to trigger CI
3. ✅ **Set up email notifications** (5 minutes)
4. ✅ **Watch for test failures** in your inbox
5. ✅ **Fix failures** using HTML reports

---

## Resources

- **Full E2E Guide**: [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)
- **Quick Reference**: [E2E_QUICKSTART.md](E2E_QUICKSTART.md)
- **Testing Strategy**: [docs/TESTING.md](docs/TESTING.md)
- **Playwright Docs**: https://playwright.dev/

---

**Status**: ✅ Ready to use right now!
**Support**: Check guides or GitHub Issues
