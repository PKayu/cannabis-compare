/**
 * E2E Test: Site Navigation and Core Pages
 *
 * Tests navigation between pages and core page rendering
 */
import { test, expect } from '@playwright/test'

// Helper to bypass age gate
async function bypassAgeGate(page) {
  await page.goto('/')
  await page.evaluate(() => localStorage.setItem('age_verified', 'true'))
  await page.reload()
}

test.describe('Site Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
  })

  test('should load home page', async ({ page }) => {
    await page.goto('/')

    // Home page should have key elements
    await expect(page).toHaveURL('/')

    // Look for site title or logo
    const hasTitle = await page.getByRole('heading', { name: /cannabis/i }).count() > 0
    const hasLogo = await page.getByAltText(/logo/i).count() > 0

    expect(hasTitle || hasLogo).toBeTruthy()
  })

  test('should display compliance disclaimer', async ({ page }) => {
    await page.goto('/')

    // Every page should have compliance disclaimer
    await expect(
      page.getByText(/informational purposes only/i)
        .or(page.getByText(/does not sell/i))
    ).toBeVisible()
  })

  test('should navigate to dispensaries page', async ({ page }) => {
    await page.goto('/')

    const dispensariesLink = page.getByRole('link', { name: /dispensar/i })

    if (await dispensariesLink.count() > 0) {
      await dispensariesLink.first().click()
      await expect(page).toHaveURL(/\/dispensaries/)

      // Should show dispensary list or map
      await expect(page.getByText(/dispensar/i)).toBeVisible()
    }
  })

  test('should have responsive navigation menu', async ({ page }) => {
    await page.goto('/')

    // Desktop view - navigation should be visible
    await page.setViewportSize({ width: 1280, height: 720 })

    const nav = page.getByRole('navigation')
      .or(page.locator('nav'))
      .or(page.locator('[role="navigation"]'))

    await expect(nav.first()).toBeVisible()

    // Mobile view - may have hamburger menu
    await page.setViewportSize({ width: 375, height: 667 })

    // Either navigation is still visible or there's a menu button
    const mobileNav = await nav.first().isVisible()
    const hasMenuButton = await page.getByRole('button', { name: /menu/i })
      .or(page.locator('[aria-label*="menu"]'))
      .count() > 0

    expect(mobileNav || hasMenuButton).toBeTruthy()
  })

  test('should handle 404 for non-existent pages', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist')

    // Should return 404 or show not found page
    expect(response?.status() === 404 || await page.getByText(/not found/i).count() > 0).toBeTruthy()
  })

  test('should maintain compliance banner across pages', async ({ page }) => {
    // Check home page
    await page.goto('/')
    await expect(page.getByText(/informational purposes only/i)).toBeVisible()

    // Navigate to search
    await page.goto('/products/search')
    await expect(page.getByText(/informational purposes only/i)).toBeVisible()

    // Navigate to dispensaries
    await page.goto('/dispensaries')
    await expect(page.getByText(/informational purposes only/i)).toBeVisible()
  })

  test('should have accessible navigation', async ({ page }) => {
    await page.goto('/')

    // Navigation should have proper ARIA labels
    const nav = page.getByRole('navigation')

    if (await nav.count() > 0) {
      // Links should be keyboard accessible
      const firstLink = nav.first().getByRole('link').first()
      await firstLink.focus()

      const isFocused = await firstLink.evaluate(el => el === document.activeElement)
      expect(isFocused).toBeTruthy()
    }
  })
})
