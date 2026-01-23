/**
 * Helper functions for E2E tests
 */
import { Page } from '@playwright/test'

/**
 * Bypass age gate by setting localStorage flag
 * Use this in beforeEach() to skip age verification for tests
 */
export async function bypassAgeGate(page: Page) {
  await page.goto('/')
  await page.evaluate(() => localStorage.setItem('age_verified', 'true'))
  await page.reload()
}

/**
 * Complete age gate with valid age (over 21)
 * Use this to test the full age verification flow
 */
export async function completeAgeGate(page: Page) {
  await page.goto('/')

  // Fill with birth date for someone 25 years old
  const birthDate = '1999-01-01'
  await page.getByLabel('Date of Birth').fill(birthDate)
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: /continue/i }).click()

  // Wait for age gate to disappear
  await page.waitForTimeout(1000)
}

/**
 * Mock authentication by setting cookies/localStorage
 * Use this to test authenticated flows without actual login
 */
export async function mockAuthentication(page: Page, userData = {
  id: 'test-user-id',
  email: 'test@example.com',
  username: 'testuser'
}) {
  // Set mock session data
  await page.evaluate((user) => {
    // This is a simplified mock - adjust based on your actual auth implementation
    localStorage.setItem('supabase.auth.token', JSON.stringify({
      access_token: 'mock-token-for-testing',
      user: user
    }))
  }, userData)
}

/**
 * Wait for API response and check status
 * Useful for verifying backend integration
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  expectedStatus = 200
) {
  const response = await page.waitForResponse(
    response => {
      const url = response.url()
      const matches = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url)
      return matches && response.status() === expectedStatus
    }
  )
  return response
}

/**
 * Take screenshot with timestamp for debugging
 */
export async function takeDebugScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/:/g, '-')
  await page.screenshot({
    path: `playwright-report/screenshots/${name}-${timestamp}.png`,
    fullPage: true
  })
}

/**
 * Check if element is in viewport
 */
export async function isInViewport(page: Page, selector: string) {
  return await page.evaluate((sel) => {
    const element = document.querySelector(sel)
    if (!element) return false

    const rect = element.getBoundingClientRect()
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    )
  }, selector)
}

/**
 * Scroll element into view
 */
export async function scrollToElement(page: Page, selector: string) {
  await page.evaluate((sel) => {
    const element = document.querySelector(sel)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, selector)
}
