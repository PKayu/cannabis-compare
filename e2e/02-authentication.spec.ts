/**
 * E2E Test: User Authentication Flow
 *
 * Tests login, profile access, and sign out functionality
 */
import { test, expect } from '@playwright/test'

// Helper to bypass age gate
async function bypassAgeGate(page) {
  await page.goto('/')
  await page.evaluate(() => localStorage.setItem('age_verified', 'true'))
  await page.reload()
}

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
  })

  test('should navigate to login page', async ({ page }) => {
    await page.goto('/')

    // Look for Sign In link/button (adjust selector based on your UI)
    const signInButton = page.getByRole('link', { name: /sign in/i })
      .or(page.getByRole('button', { name: /sign in/i }))

    if (await signInButton.count() > 0) {
      await signInButton.first().click()
      await expect(page).toHaveURL(/\/auth\/login/)
    } else {
      // If no sign in button on home page, navigate directly
      await page.goto('/auth/login')
    }

    // Verify login page loaded
    await expect(page.getByText(/sign in/i).or(page.getByText(/log in/i))).toBeVisible()
  })

  test('should show magic link form', async ({ page }) => {
    await page.goto('/auth/login')

    // Should have email input
    await expect(page.getByLabel(/email/i)).toBeVisible()

    // Should have submit button
    await expect(page.getByRole('button', { name: /send.*link/i })
      .or(page.getByRole('button', { name: /continue/i }))).toBeVisible()
  })

  test('should validate email input', async ({ page }) => {
    await page.goto('/auth/login')

    const emailInput = page.getByLabel(/email/i)
    const submitButton = page.getByRole('button', { name: /send.*link/i })
      .or(page.getByRole('button', { name: /continue/i }))

    // Try submitting with invalid email
    await emailInput.fill('not-an-email')
    await submitButton.first().click()

    // Browser validation should prevent submission
    // or app should show error message
    const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage)
    expect(validationMessage.length).toBeGreaterThan(0)
  })

  test('should submit magic link request', async ({ page }) => {
    await page.goto('/auth/login')

    const emailInput = page.getByLabel(/email/i)
    const submitButton = page.getByRole('button', { name: /send.*link/i })
      .or(page.getByRole('button', { name: /continue/i }))

    // Fill valid email
    await emailInput.fill('test@example.com')
    await submitButton.first().click()

    // Should show success message or loading state
    // Adjust based on your actual UI feedback
    await expect(
      page.getByText(/check.*email/i)
        .or(page.getByText(/sending/i))
        .or(page.getByText(/sent/i))
    ).toBeVisible({ timeout: 10000 })
  })

  test('should protect profile page when not authenticated', async ({ page }) => {
    // Clear any existing session
    await page.context().clearCookies()
    await page.evaluate(() => localStorage.clear())

    // Try to access profile directly
    await page.goto('/profile')

    // Should redirect to login or show not authenticated message
    await expect(
      page.waitForURL(/\/auth\/login/, { timeout: 5000 })
        .catch(() => page.getByText(/not.*authenticated/i).isVisible())
    ).resolves.toBeTruthy()
  })

  test('should show Google OAuth option', async ({ page }) => {
    await page.goto('/auth/login')

    // Should have Google sign-in button
    const googleButton = page.getByRole('button', { name: /google/i })
      .or(page.getByText(/sign in with google/i))

    await expect(googleButton).toBeVisible()
  })
})
