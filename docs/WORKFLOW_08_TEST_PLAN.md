# Workflow 08: User Authentication - Test Plan

**Workflow**: 08 - User Authentication
**Phase**: Community Features (Phase 3)
**Date Created**: January 22, 2026
**Status**: Ready for Testing
**Implementation Status**: Complete (All 13 Steps)

---

## Overview

This document outlines the comprehensive test plan for Workflow 08: User Authentication. It includes all scenarios, expected results, and debugging guides to verify the authentication system works correctly.

---

## Pre-Testing Checklist

Before starting any tests, ensure:

- [ ] Backend is running: `uvicorn main:app --reload` (port 8000)
- [ ] Frontend is running: `npm run dev` (port 3000)
- [ ] PostgreSQL database is connected and accessible
- [ ] Supabase credentials configured in `frontend/.env.local`
- [ ] Supabase credentials configured in `backend/.env`
- [ ] All dependencies installed (`npm install`, `pip install`)
- [ ] No TypeScript compilation errors
- [ ] Browser cache cleared (optional but recommended)
- [ ] Using Chrome, Firefox, or Edge (recommended for testing)

**Command to Verify Backend Health**:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "version": "0.1.0"}
```

---

## Test Scenarios

### Test 1: Age Gate Verification

**Test ID**: AUTH-001
**Objective**: Verify age gate displays and validates age correctly
**Priority**: Critical
**Estimated Time**: 5 minutes

#### Pre-Conditions
- Fresh browser session (clear cache/cookies or use private/incognito window)
- Frontend running on port 3000

#### Steps

1. **Initial Display**
   - [ ] Navigate to `http://localhost:3000`
   - [ ] Age gate modal should appear immediately as full-screen overlay
   - [ ] Modal should show: "Age Verification Required" heading
   - [ ] Modal should have date input, checkbox, and "Continue" button
   - [ ] "Continue" button should be disabled initially

2. **Attempt Under 21**
   - [ ] Enter birth date from 2010 (e.g., 01/15/2010)
   - [ ] "Continue" button remains disabled (no checkbox)
   - [ ] Click checkbox: "I confirm I am 21 years or older..."
   - [ ] "Continue" button becomes enabled
   - [ ] Click "Continue"
   - [ ] Error message appears: "You must be 21 years or older to access this site."
   - [ ] Modal remains open (not dismissed)
   - [ ] User can try again

3. **Successful Verification (Over 21)**
   - [ ] Clear birth date field
   - [ ] Enter birth date from 2000 (e.g., 06/15/2000)
   - [ ] Click checkbox
   - [ ] Click "Continue"
   - [ ] Age gate modal disappears
   - [ ] Home page content loads behind modal
   - [ ] No error message displayed

4. **Persistence Check**
   - [ ] Refresh page (Ctrl+R or Cmd+R)
   - [ ] Age gate should NOT appear again
   - [ ] Home page loads immediately

5. **localStorage Verification**
   - [ ] Open DevTools (F12)
   - [ ] Go to Application → Local Storage
   - [ ] Find entry with key: `age_verified`
   - [ ] Value should be: `true`

#### Expected Results
- [ ] Age gate appears on first visit
- [ ] Age calculation is accurate (21+ check)
- [ ] Error shown for underage users
- [ ] Age verification persists after refresh
- [ ] localStorage contains `age_verified: true`

#### Pass Criteria
All steps completed successfully

---

### Test 2: Magic Link Login Flow

**Test ID**: AUTH-002
**Objective**: Verify magic link email authentication works end-to-end
**Priority**: Critical
**Estimated Time**: 10 minutes

#### Pre-Conditions
- Age gate verified
- Access to email inbox or Supabase dashboard
- Frontend running on port 3000

#### Steps

1. **Navigate to Login**
   - [ ] Click "Sign In" button (if visible on home page)
   - [ ] Or navigate directly to `http://localhost:3000/auth/login`
   - [ ] Login page should load with email input form

2. **Enter Email and Request Magic Link**
   - [ ] Enter test email address: `test.auth@example.com`
   - [ ] Verify email input accepts valid email format
   - [ ] Click "Send Magic Link" button
   - [ ] Button should show loading state: "Sending..."
   - [ ] Wait for response

3. **Verify Success Message**
   - [ ] Green success message appears: "Check your email for the login link! It will expire in 24 hours."
   - [ ] Email input field is cleared
   - [ ] User can enter another email if desired

4. **Check User in Supabase Dashboard**
   - [ ] Go to Supabase Dashboard
   - [ ] Navigate to Authentication → Users
   - [ ] Verify new user appears in list
   - [ ] User email should match entered email
   - [ ] User status should show as authenticated

5. **Verify Magic Link Email**
   - [ ] **Note**: In development, actual email may not send
   - [ ] Check your email inbox for message from Supabase
   - [ ] Or in Supabase, check Auth → Email Templates to verify configuration
   - [ ] Magic link should include redirect to `/auth/callback`

#### Expected Results
- [ ] Login page loads correctly
- [ ] Email submission succeeds
- [ ] Success message displays
- [ ] User created in Supabase
- [ ] Magic link email configured (actual email may not send in dev)

#### Pass Criteria
- User successfully created in Supabase Auth
- Success message displayed
- No console errors

---

### Test 3: Google OAuth Login

**Test ID**: AUTH-003
**Objective**: Verify Google OAuth authentication
**Priority**: High
**Estimated Time**: 8 minutes

#### Pre-Conditions
- Age gate verified
- Google account available for testing
- Google OAuth credentials configured in Supabase
- Frontend running on port 3000

#### Steps

1. **Navigate to Login**
   - [ ] Go to `http://localhost:3000/auth/login`
   - [ ] Verify "Sign in with Google" button is visible below divider

2. **Click Google OAuth Button**
   - [ ] Click "Sign in with Google" button
   - [ ] Should redirect to Google login page
   - [ ] Google login modal or page should appear

3. **Complete Google Authentication**
   - [ ] Sign in with your Google account
   - [ ] Verify email and password
   - [ ] Google may ask for permissions (first time only)
   - [ ] Click "Allow" if prompted

4. **Verify Redirect to Callback**
   - [ ] After Google auth succeeds, redirect to `/auth/callback`
   - [ ] Callback page should show "Verifying your credentials..." with loading spinner
   - [ ] Wait for verification to complete

5. **Verify Redirect to Profile**
   - [ ] After verification, should redirect to `/profile` page
   - [ ] Profile page should load successfully
   - [ ] User information should display (email, username, etc.)

6. **Verify User in Supabase**
   - [ ] Go to Supabase Dashboard → Auth → Users
   - [ ] New user should appear with Google OAuth provider
   - [ ] User identity provider should show "google"

#### Expected Results
- [ ] Google sign-in button visible and clickable
- [ ] Redirects to Google login
- [ ] Returns to callback handler
- [ ] Automatically redirects to profile
- [ ] User created in Supabase with Google provider
- [ ] Profile page loads with authenticated user

#### Pass Criteria
- Complete OAuth flow without errors
- User successfully created via Google OAuth
- Redirects to profile after auth

---

### Test 4: User Profile Page

**Test ID**: AUTH-004
**Objective**: Verify authenticated users can view and manage profile
**Priority**: Critical
**Estimated Time**: 10 minutes

#### Pre-Conditions
- Successfully signed in (via magic link or OAuth)
- Profile page loads without redirect
- Backend running with database connected

#### Steps

1. **Profile Page Load**
   - [ ] Navigate to or be redirected to `/profile`
   - [ ] Page should load within 2 seconds
   - [ ] No loading spinner (if session is valid)
   - [ ] No error messages displayed

2. **Verify Profile Information Section**
   - [ ] "Account Information" card visible
   - [ ] Email field shows your login email
   - [ ] Username field populated correctly
   - [ ] "Member Since" shows today's date
   - [ ] "Reviews Posted" shows 0 (initially)

3. **Verify Reviews Section**
   - [ ] "My Reviews" section visible
   - [ ] Empty state message: "You haven't posted any reviews yet."
   - [ ] "Browse Products" button visible and clickable
   - [ ] Clicking "Browse Products" navigates to `/products/search`

4. **Verify User Navigation Menu**
   - [ ] User avatar (circle with initials) visible in top-right
   - [ ] Clicking avatar opens dropdown menu
   - [ ] Dropdown shows:
     - [ ] Current email address
     - [ ] "My Profile" link
     - [ ] "My Reviews" link
     - [ ] "Watchlist" link (disabled, coming soon)
     - [ ] "Sign Out" button

5. **Test Sign Out**
   - [ ] Click "Sign Out" button in dropdown
   - [ ] Should redirect to home page (`/`)
   - [ ] Profile page no longer accessible (redirects to login)
   - [ ] Session cleared from browser storage

6. **Verify Session Cleared**
   - [ ] Open DevTools → Application → Cookies
   - [ ] Supabase auth session should be empty/removed
   - [ ] Try accessing `/profile` directly
   - [ ] Should redirect to `/auth/login`

#### Expected Results
- [ ] Profile page loads with correct user data
- [ ] All sections display properly
- [ ] Sign out clears session
- [ ] Profile protected after logout

#### Pass Criteria
- Profile data displays correctly
- Sign out functionality works
- Protected routes enforce authentication

---

### Test 5: Protected Routes

**Test ID**: AUTH-005
**Objective**: Verify unauthenticated users cannot access protected routes
**Priority**: Critical
**Estimated Time**: 5 minutes

#### Pre-Conditions
- Not signed in (or signed out)
- Fresh browser session or private window
- Frontend running on port 3000

#### Steps

1. **Attempt Direct Access to Profile**
   - [ ] Navigate directly to `http://localhost:3000/profile`
   - [ ] Should redirect to `/auth/login` immediately
   - [ ] No profile data shown
   - [ ] Login form displayed

2. **Test Route Guard Behavior**
   - [ ] Verify redirect happens before profile loads
   - [ ] URL should change to `/auth/login`
   - [ ] Loading spinner should appear briefly during check

3. **Sign In and Return URL Handling**
   - [ ] Sign in with email or Google
   - [ ] Should ideally return to original URL (`/profile`)
   - [ ] Or at minimum, redirect to profile after login

#### Expected Results
- [ ] Unauthenticated users cannot access `/profile`
- [ ] Automatic redirect to login page
- [ ] No data leakage or errors

#### Pass Criteria
- All protected routes redirect to login
- Clear URL transitions
- No console errors

---

### Test 6: API Authentication with JWT

**Test ID**: AUTH-006
**Objective**: Verify JWT tokens are correctly attached to API requests
**Priority**: High
**Estimated Time**: 10 minutes

#### Pre-Conditions
- Signed in to profile page
- DevTools available
- Backend running with auth endpoints

#### Steps

1. **Monitor API Requests**
   - [ ] Go to `/profile` (while signed in)
   - [ ] Open DevTools (F12)
   - [ ] Go to Network tab
   - [ ] Refresh page to capture requests

2. **Check Authorization Header**
   - [ ] Find request: `GET /api/users/me`
   - [ ] Click on request to view details
   - [ ] Go to "Request Headers" tab
   - [ ] Verify header exists: `Authorization: Bearer <token>`
   - [ ] Token should be long string of base64-encoded JWT
   - [ ] Format should be exactly: `Bearer <token>` (space between)

3. **Verify Request is Successful**
   - [ ] Response status should be 200
   - [ ] Response body contains user data (email, username, etc.)
   - [ ] No 401 Unauthorized errors

4. **Test Invalid Token Handling**
   - [ ] Open DevTools Console
   - [ ] Type: `localStorage.setItem('test-invalid-token', 'invalid')`
   - [ ] Make a new API call using fetch:
     ```javascript
     fetch('http://localhost:8000/api/users/me', {
       headers: {'Authorization': 'Bearer invalid'}
     }).then(r => r.json()).then(console.log)
     ```
   - [ ] Should get 401 Unauthorized response
   - [ ] Error message: "Invalid or expired token"

5. **Test Token Refresh**
   - [ ] While on profile page, wait a few minutes
   - [ ] Make a new API request
   - [ ] Token should still work (session persisted)
   - [ ] No 401 errors

#### Expected Results
- [ ] JWT tokens attached to all requests
- [ ] Valid tokens accepted by backend
- [ ] Invalid tokens return 401
- [ ] Authorization header format correct

#### Pass Criteria
- All authenticated requests include valid tokens
- Invalid tokens properly rejected
- Token format matches Bearer scheme

---

### Test 7: Backend Auth Endpoints

**Test ID**: AUTH-007
**Objective**: Verify backend authentication endpoints work correctly
**Priority**: High
**Estimated Time**: 15 minutes

#### Pre-Conditions
- Backend running on port 8000
- Curl or Postman installed
- Test email address ready

#### Steps

1. **Test Registration Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "newuser@example.com",
       "username": "newuser123",
       "password": "SecurePass123!"
     }'
   ```
   - [ ] Response status: 200
   - [ ] Response includes: `access_token`, `token_type`, `user_id`
   - [ ] `token_type` should be: `bearer`
   - [ ] `access_token` is long JWT string

2. **Test Login Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "newuser@example.com",
       "password": "SecurePass123!"
     }'
   ```
   - [ ] Response status: 200
   - [ ] Returns same token structure as register
   - [ ] Same user_id as registration

3. **Test Invalid Password**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "newuser@example.com",
       "password": "WrongPassword"
     }'
   ```
   - [ ] Response status: 401
   - [ ] Error message: "Invalid email or password"
   - [ ] No user data leaked

4. **Test Get Profile Endpoint**
   ```bash
   # Replace TOKEN with actual token from login response
   curl http://localhost:8000/api/users/me \
     -H "Authorization: Bearer TOKEN"
   ```
   - [ ] Response status: 200
   - [ ] Returns user object with: id, email, username, created_at, review_count
   - [ ] Data matches registration

5. **Test Protected Endpoint Without Token**
   ```bash
   curl http://localhost:8000/api/users/me
   ```
   - [ ] Response status: 401
   - [ ] Error message: "Missing authorization header"

6. **Test Protected Endpoint with Invalid Token**
   ```bash
   curl http://localhost:8000/api/users/me \
     -H "Authorization: Bearer invalid_token_here"
   ```
   - [ ] Response status: 401
   - [ ] Error message: "Invalid or expired token"

7. **Test Token Refresh Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/auth/refresh \
     -H "Authorization: Bearer TOKEN"
   ```
   - [ ] Response status: 200
   - [ ] Returns new access_token
   - [ ] New token is valid JWT

8. **Test Verify Token Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/auth/verify-token \
     -H "Content-Type: application/json" \
     -d '{"token": "TOKEN"}'
   ```
   - [ ] Response status: 200
   - [ ] Returns: `{"valid": true, "user_id": "...", "email": "..."}`

#### Expected Results
- [ ] All endpoints respond with correct status codes
- [ ] Token generation works correctly
- [ ] Authentication required for protected endpoints
- [ ] Proper error messages for invalid requests

#### Pass Criteria
- All endpoints return expected responses
- Security properly enforced
- Token format and validation correct

---

### Test 8: Session Persistence

**Test ID**: AUTH-008
**Objective**: Verify sessions persist across page refreshes and browser restarts
**Priority**: High
**Estimated Time**: 10 minutes

#### Pre-Conditions
- Signed in and on profile page
- Session token stored in browser

#### Steps

1. **Test Page Refresh**
   - [ ] Go to `/profile`
   - [ ] Verify profile loads with user data
   - [ ] Press Ctrl+R (or Cmd+R) to refresh
   - [ ] Profile should reload immediately without redirecting to login
   - [ ] No "Loading..." message should appear
   - [ ] User data should persist

2. **Test Navigation Away and Back**
   - [ ] From profile, navigate to `/products/search`
   - [ ] Then navigate back to `/profile`
   - [ ] Profile should load without re-authentication
   - [ ] User data should be current

3. **Test Browser Close and Reopen**
   - [ ] Sign in and go to `/profile`
   - [ ] Close the browser completely (not just tab)
   - [ ] Reopen browser and go to `http://localhost:3000`
   - [ ] Go to `/profile` directly
   - [ ] **Result will depend on Supabase session configuration**:
     - [ ] If session is persisted: Profile loads directly
     - [ ] If session expired: Redirects to login (acceptable)

4. **Verify Session Storage**
   - [ ] Open DevTools → Application
   - [ ] Check Local Storage: Should contain Supabase session data
   - [ ] Check Session Storage: May contain temporary data
   - [ ] Check Cookies: May contain auth tokens

#### Expected Results
- [ ] Page refreshes don't require re-authentication
- [ ] Navigation preserves session
- [ ] Session data properly stored in browser

#### Pass Criteria
- Sessions persist across refreshes
- No unexpected redirects to login
- User remains authenticated during session

---

### Test 9: Error Handling and Edge Cases

**Test ID**: AUTH-009
**Objective**: Verify proper error handling in various scenarios
**Priority**: Medium
**Estimated Time**: 10 minutes

#### Steps

1. **Test Empty Form Submission**
   - [ ] On login page, click "Send Magic Link" without email
   - [ ] Form validation should prevent submission
   - [ ] Error message about required field

2. **Test Duplicate Email Registration**
   - [ ] Attempt to register with already-used email
   - [ ] Should get error: "Email already registered" or from Supabase

3. **Test Weak Password**
   - [ ] Try to register with password like "123"
   - [ ] Should get validation error from Supabase

4. **Test Network Error Handling**
   - [ ] Disconnect internet while on login page
   - [ ] Try to send magic link
   - [ ] Should show appropriate error message
   - [ ] Not a blank error or console error

5. **Test Expired Token on API Call**
   - [ ] Make a request with manually invalid token
   - [ ] Should redirect to login page
   - [ ] Session should be cleared

#### Expected Results
- [ ] Graceful error handling throughout
- [ ] User-friendly error messages
- [ ] No console errors leaking data

#### Pass Criteria
- All edge cases handled properly
- Clear error messaging
- No crashes or unhandled exceptions

---

### Test 10: Review History Display

**Test ID**: AUTH-010
**Objective**: Verify review history displays correctly (placeholder phase)
**Priority**: Low
**Estimated Time**: 5 minutes
**Note**: Full reviews implemented in Workflow 09

#### Steps

1. **Check Empty Reviews**
   - [ ] Go to `/profile`
   - [ ] "My Reviews" section shows: "You haven't posted any reviews yet."
   - [ ] "Browse Products" link is present and clickable

2. **Verify Link Navigation**
   - [ ] Click "Browse Products"
   - [ ] Navigates to `/products/search`

#### Expected Results
- [ ] Placeholder text shown when no reviews
- [ ] Links work correctly

#### Pass Criteria
- Empty state displays properly
- Navigation links work

---

## TypeScript and Code Quality Tests

### Test 11: TypeScript Compilation

**Test ID**: QUALITY-001
**Objective**: Verify no TypeScript errors
**Priority**: High
**Estimated Time**: 5 minutes

#### Steps

```bash
cd frontend
npm run type-check
```

- [ ] Command completes without errors
- [ ] No error messages in output
- [ ] May show warnings (acceptable)

#### Expected Results
- [ ] No TypeScript compilation errors
- [ ] All type definitions properly used

---

### Test 12: Python Type Checking (Optional)

**Test ID**: QUALITY-002
**Objective**: Verify no Python type errors
**Priority**: Medium
**Estimated Time**: 5 minutes

#### Steps

```bash
cd backend
pip install mypy
mypy routers/auth.py routers/users.py services/
```

- [ ] Command completes successfully
- [ ] No error messages for undefined types
- [ ] May show info messages (acceptable)

#### Expected Results
- [ ] No Python type errors
- [ ] Code follows typing conventions

---

## Accessibility and Responsive Design Tests

### Test 13: Mobile Responsiveness

**Test ID**: UX-001
**Objective**: Verify UI works on mobile devices
**Priority**: High
**Estimated Time**: 10 minutes

#### Steps

1. **Login Page Mobile**
   - [ ] Open DevTools → Device Toolbar
   - [ ] Select iPhone 12 or similar
   - [ ] Login form should be responsive
   - [ ] Buttons should be touch-friendly (44px+ height)
   - [ ] Text should be readable
   - [ ] No horizontal scrolling needed

2. **Profile Page Mobile**
   - [ ] Profile cards should stack vertically
   - [ ] User dropdown should work on touch
   - [ ] Review list should be scrollable
   - [ ] No layout issues

3. **Age Gate Mobile**
   - [ ] Modal should fit screen
   - [ ] Date input should be usable
   - [ ] Button should be easily clickable

#### Expected Results
- [ ] All pages responsive on mobile
- [ ] Touch-friendly UI elements
- [ ] No overflow or layout issues

#### Pass Criteria
- Mobile responsive design working
- Touch interactions functional

---

### Test 14: Keyboard Navigation

**Test ID**: UX-002
**Objective**: Verify keyboard accessibility
**Priority**: Medium
**Estimated Time**: 5 minutes

#### Steps

1. **Age Gate**
   - [ ] Press Tab to navigate between inputs
   - [ ] Space/Enter to toggle checkbox
   - [ ] Enter to submit form

2. **Login Form**
   - [ ] Tab through email input → button
   - [ ] Enter to submit
   - [ ] Focus states visible

3. **Profile Dropdown**
   - [ ] Tab to focus user menu button
   - [ ] Enter/Space to open dropdown
   - [ ] Tab to navigate menu items
   - [ ] Escape to close

#### Expected Results
- [ ] Full keyboard navigation possible
- [ ] Focus states visible
- [ ] No keyboard traps

#### Pass Criteria
- All features accessible via keyboard
- Focus management proper

---

## Test Execution Log

Use this section to track test execution:

```
Date: __________
Tester: __________
Environment: Development / Staging / Production

Test Results:
- AUTH-001 (Age Gate): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-002 (Magic Link): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-003 (Google OAuth): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-004 (Profile Page): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-005 (Protected Routes): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-006 (JWT Auth): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-007 (Backend Endpoints): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-008 (Session Persistence): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-009 (Error Handling): [ ] PASS [ ] FAIL [ ] SKIPPED
- AUTH-010 (Review History): [ ] PASS [ ] FAIL [ ] SKIPPED
- QUALITY-001 (TypeScript): [ ] PASS [ ] FAIL [ ] SKIPPED
- QUALITY-002 (Python Types): [ ] PASS [ ] FAIL [ ] SKIPPED
- UX-001 (Mobile): [ ] PASS [ ] FAIL [ ] SKIPPED
- UX-002 (Keyboard): [ ] PASS [ ] FAIL [ ] SKIPPED

Overall Result: [ ] ALL PASS [ ] SOME FAILURES [ ] BLOCKED

Notes:
_________________________________________________________________________
_________________________________________________________________________
```

---

## Debugging Guide

### Issue: Age Gate Shows Every Visit

**Symptom**: Age gate appears even after verification

**Debugging Steps**:
1. Open DevTools → Application → Local Storage
2. Check for key: `age_verified`
3. If missing, age gate verification didn't save

**Solution**:
- Check browser allows localStorage (not incognito in some cases)
- Verify AgeGate component is writing to localStorage
- Check browser console for JavaScript errors

---

### Issue: 401 Unauthorized on API Calls

**Symptom**: API calls return 401 even when logged in

**Debugging Steps**:
1. DevTools → Network tab → Any API call
2. Check Request Headers → Authorization
3. Should see: `Authorization: Bearer <token>`

**Solutions**:
- If header missing: Supabase session not found
- If token invalid: Session expired, need to sign in again
- If 401 but header present: Backend JWT verification failing

**Check Backend**:
```python
# Verify credentials in backend/.env
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
SECRET_KEY=...
```

---

### Issue: Profile Page Shows "Not Logged In"

**Symptom**: Profile page shows error or redirects to login

**Debugging Steps**:
1. Check Supabase session: DevTools → Application → Cookies/Local Storage
2. Check network request to `/api/users/me`
3. What is response status code?

**Solutions**:
- **401 response**: Token invalid or expired
- **500 response**: Backend error, check server logs
- **No request**: API client not attaching token
- **Redirect to login**: Session doesn't exist in Supabase

---

### Issue: Google OAuth Not Working

**Symptom**: Clicking Google button does nothing or shows error

**Debugging Steps**:
1. Check browser console for errors
2. Verify Supabase OAuth configuration
3. Check redirect URL is whitelisted

**Solutions**:
- Verify OAuth credentials in Supabase
- Check redirect URLs in Google Cloud Console include `http://localhost:3000/auth/callback`
- Verify in Supabase settings:
  - OAuth enabled
  - Client ID and Secret correct
  - Redirect URL configured

---

### Issue: Magic Link Not Sending

**Symptom**: Form submits but no email received

**Debugging Steps**:
1. Check Supabase Dashboard → Users
2. If user appears: Email service not configured
3. If user doesn't appear: Error occurred

**Solutions**:
- In dev: Supabase may not send actual emails
- Check Supabase Email Templates configured
- Test with Supabase's test mode
- For production: Configure SMTP provider

---

### Issue: TypeScript Errors

**Symptom**: `npm run type-check` shows errors

**Common Solutions**:
- Missing type imports: `import type { ... } from '...'`
- Props interface not matching usage
- Async/await issues with types
- Missing `@ts-ignore` comments (if intentional)

**Run full check**:
```bash
npm run type-check 2>&1 | head -20  # See first 20 errors
```

---

### Issue: Session Not Persisting

**Symptom**: Page refresh redirects to login

**Debugging Steps**:
1. Check Supabase session exists: DevTools → Application
2. Verify `supabase.auth.getSession()` returns session
3. Check browser Settings → Cookies

**Solutions**:
- May be expected behavior (depends on Supabase config)
- Check session timeout settings
- Verify localStorage not cleared
- Try different browser

---

## Success Criteria Summary

### Critical (Must Pass)
- [ ] Age gate displays and validates correctly
- [ ] Magic link or OAuth authentication works
- [ ] Authenticated users can access profile
- [ ] Protected routes redirect to login
- [ ] No TypeScript errors
- [ ] All backend endpoints respond correctly

### High Priority (Should Pass)
- [ ] JWT tokens properly attached to requests
- [ ] Session persists across page refreshes
- [ ] Error messages are helpful
- [ ] Mobile responsive design works

### Medium Priority (Nice to Have)
- [ ] Keyboard navigation works
- [ ] Python type checking passes
- [ ] All edge cases handled gracefully

### Overall Pass Criteria
- **14 tests total**
- **Minimum 12/14 passing** (85%) to consider workflow complete
- **All critical tests must pass**
- **No blocking bugs**

---

## Sign-Off

After completing all tests:

- **Tester Name**: ___________________
- **Date Completed**: ___________________
- **Overall Status**: [ ] PASS [ ] FAIL [ ] CONDITIONAL
- **Notes**: ________________________________________________________________

**Approved for Production**: [ ] YES [ ] NO

---

**Last Updated**: January 22, 2026
**Version**: 1.0
**Owner**: Authentication Team
