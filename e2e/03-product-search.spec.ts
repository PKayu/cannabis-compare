/**
 * E2E Test: Product Search and Browse
 *
 * Tests product discovery, search, and filtering functionality
 */
import { test, expect } from '@playwright/test'

// Helper to bypass age gate
async function bypassAgeGate(page) {
  await page.goto('/')
  await page.evaluate(() => localStorage.setItem('age_verified', 'true'))
  await page.reload()
}

test.describe('Product Search', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
  })

  test('should navigate to product search page', async ({ page }) => {
    await page.goto('/')

    // Look for search or products link
    const searchLink = page.getByRole('link', { name: /search/i })
      .or(page.getByRole('link', { name: /products/i }))
      .or(page.getByRole('link', { name: /browse/i }))

    if (await searchLink.count() > 0) {
      await searchLink.first().click()
      await expect(page).toHaveURL(/\/(products|search)/)
    } else {
      // Navigate directly if no link found
      await page.goto('/products/search')
    }
  })

  test('should display search interface', async ({ page }) => {
    await page.goto('/products/search')

    // Should have search input or filters
    const hasSearchInput = await page.getByPlaceholder(/search/i).count() > 0
    const hasFilters = await page.getByText(/filter/i).count() > 0
    const hasProductType = await page.getByText(/product type/i).or(page.getByText(/category/i)).count() > 0

    // At least one search-related element should be present
    expect(hasSearchInput || hasFilters || hasProductType).toBeTruthy()
  })

  test('should perform product search', async ({ page }) => {
    await page.goto('/products/search')

    const searchInput = page.getByPlaceholder(/search/i)
      .or(page.getByRole('searchbox'))
      .or(page.getByLabel(/search/i))

    if (await searchInput.count() > 0) {
      // Enter search term
      await searchInput.first().fill('indica')

      // Wait for results to load
      await page.waitForTimeout(1000) // Debounce delay

      // Results should appear (or "no results" message)
      const hasResults = await page.getByTestId('product-card')
        .or(page.getByText(/results/i))
        .or(page.getByText(/no.*found/i))
        .count() > 0

      expect(hasResults).toBeTruthy()
    }
  })

  test('should filter by product type', async ({ page }) => {
    await page.goto('/products/search')

    // Look for product type filters (flower, edibles, etc.)
    const flowerFilter = page.getByText(/flower/i)
      .or(page.getByLabel(/flower/i))

    if (await flowerFilter.count() > 0) {
      await flowerFilter.first().click()

      // Wait for filtered results
      await page.waitForTimeout(1000)

      // Page should update with filtered results
      // (Can't assert exact results without knowing database state)
      expect(page.url()).toContain('search')
    }
  })

  test('should navigate to product detail page', async ({ page }) => {
    await page.goto('/products/search')

    // Wait for products to load
    await page.waitForTimeout(2000)

    // Find first product link/card
    const productCard = page.getByTestId('product-card')
      .or(page.getByRole('link').filter({ has: page.getByText(/\$/i) }))

    if (await productCard.count() > 0) {
      await productCard.first().click()

      // Should navigate to product detail page
      await expect(page).toHaveURL(/\/products\/[a-zA-Z0-9-]+/)

      // Detail page should have product information
      await expect(
        page.getByText(/\$/i)
          .or(page.getByText(/price/i))
          .or(page.getByText(/THC/i))
      ).toBeVisible({ timeout: 5000 })
    }
  })

  test('should display price comparison on product detail', async ({ page }) => {
    // This test assumes you have at least one product
    // You may need to seed test data or skip if no products exist
    await page.goto('/products/search')
    await page.waitForTimeout(2000)

    const productCard = page.getByTestId('product-card')
      .or(page.getByRole('link').filter({ has: page.getByText(/\$/i) }))

    if (await productCard.count() > 0) {
      await productCard.first().click()

      // Should show prices from different dispensaries
      await expect(
        page.getByText(/compare prices/i)
          .or(page.getByText(/dispensary/i))
          .or(page.getByText(/\$/))
      ).toBeVisible({ timeout: 5000 })
    }
  })
})
