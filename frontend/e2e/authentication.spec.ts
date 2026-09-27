import { expect, test } from '@playwright/test'
import { bypassAgeGate, mockEmptyApi } from './helpers'

test.describe('Authentication entry', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
    await mockEmptyApi(page)
  })

  test('navigates from the public shell to the sign-in form', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'Sign in' }).click()

    await expect(page).toHaveURL(/\/auth\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible()
    await expect(page.getByLabel('Email Address')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Send Magic Link' })).toBeDisabled()
    await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible()
  })

  test('uses native email validation before contacting the auth provider', async ({ page }) => {
    await page.goto('/auth/login')
    const email = page.getByLabel('Email Address')
    await email.fill('not-an-email')
    await page.getByRole('button', { name: 'Send Magic Link' }).click()

    expect(await email.evaluate((input: HTMLInputElement) => input.validationMessage)).not.toBe('')
  })

  test('shows the success state for a deterministic magic-link request', async ({ page }) => {
    await page.route('https://test.supabase.co/auth/v1/otp**', route => route.fulfill({
      status: 200,
      headers: { 'access-control-allow-origin': '*', 'content-type': 'application/json' },
      body: '{}',
    }))
    await page.goto('/auth/login?returnUrl=%2Fwatchlist')
    await page.getByLabel('Email Address').fill('patient@example.com')
    await page.getByRole('button', { name: 'Send Magic Link' }).click()

    await expect(page.getByText(/check your email for the login link/i)).toBeVisible()
    await expect(page.getByLabel('Email Address')).toHaveValue('')
  })

  test('preserves the intended path when a signed-out user opens a protected route', async ({ page }) => {
    await page.goto('/profile')

    await expect(page).toHaveURL(/\/auth\/login\?returnUrl=%2Fprofile$/)
    await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible()
  })
})
