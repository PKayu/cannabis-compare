/**
 * E2E Test: Age Gate Verification
 *
 * Tests the critical age verification flow that protects the entire site
 */
import { test, expect } from '@playwright/test'

test.describe('Age Gate', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to ensure age gate shows
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
  })

  test('should show age gate on first visit', async ({ page }) => {
    await page.goto('/')

    // Age gate should be visible
    await expect(page.getByText('Welcome! Let's verify your age')).toBeVisible()
    await expect(page.getByLabel('Date of Birth')).toBeVisible()
    await expect(page.getByRole('button', { name: /continue/i })).toBeVisible()
  })

  test('should reject users under 21', async ({ page }) => {
    await page.goto('/')

    // Calculate birth date for someone who is 18
    const today = new Date()
    const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate())
    const birthDate = eighteenYearsAgo.toISOString().split('T')[0]

    // Fill form
    await page.getByLabel('Date of Birth').fill(birthDate)
    await page.getByRole('checkbox').check()
    await page.getByRole('button', { name: /continue/i }).click()

    // Should show error
    await expect(page.getByText(/you must be 21 years or older/i)).toBeVisible()

    // Should still be on age gate (not dismissed)
    await expect(page.getByText('Welcome! Let's verify your age')).toBeVisible()
  })

  test('should accept users over 21 and persist verification', async ({ page }) => {
    await page.goto('/')

    // Fill with valid age (25 years old)
    const birthDate = '1999-01-01'
    await page.getByLabel('Date of Birth').fill(birthDate)
    await page.getByRole('checkbox').check()
    await page.getByRole('button', { name: /continue/i }).click()

    // Age gate should disappear and home page should load
    await expect(page.getByText('Welcome! Let's verify your age')).not.toBeVisible({ timeout: 5000 })

    // Verify localStorage was set
    const ageVerified = await page.evaluate(() => localStorage.getItem('age_verified'))
    expect(ageVerified).toBe('true')

    // Refresh page - age gate should NOT appear again
    await page.reload()
    await expect(page.getByText('Welcome! Let's verify your age')).not.toBeVisible()
  })

  test('should require both date and checkbox', async ({ page }) => {
    await page.goto('/')

    const continueButton = page.getByRole('button', { name: /continue/i })

    // Button should be disabled initially
    await expect(continueButton).toBeDisabled()

    // Fill date only
    await page.getByLabel('Date of Birth').fill('1999-01-01')
    await expect(continueButton).toBeDisabled()

    // Check checkbox
    await page.getByRole('checkbox').check()
    await expect(continueButton).toBeEnabled()
  })
})
