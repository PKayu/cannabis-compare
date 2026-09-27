import { expect, test, type Page } from '@playwright/test'
import { results } from '../ux-tests/fixtures'
import { bypassAgeGate } from './helpers'

async function mockSearchApi(page: Page) {
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/products/autocomplete') {
      return route.fulfill({
        json: [{ id: 'master', name: 'Blue Dream', brand: 'Example Grower', type: 'flower' }],
      })
    }
    if (path === '/api/products/search') return route.fulfill({ json: results })
    return route.fulfill({ json: [] })
  })
}

test.describe('Product discovery', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
    await mockSearchApi(page)
  })

  test('starts a supported search from the homepage', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Find your next stop.' })).toBeVisible()
    const search = page.getByRole('combobox', { name: 'Search products or brands' })
    await search.fill('blue')
    await expect(page.getByRole('option', { name: /Blue Dream/ })).toBeVisible()
    await search.press('ArrowDown')
    await search.press('Enter')

    await expect(page).toHaveURL('/products/search?q=Blue%20Dream')
    await expect(page.getByText('2 products found')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Blue Dream', exact: true })).toBeVisible()
  })

  test('enforces the two-character query contract without making a request', async ({ page }) => {
    let requests = 0
    await page.route('**/api/products/search**', route => {
      requests += 1
      return route.fulfill({ json: results })
    })
    await page.goto('/products/search?q=b')

    await expect(page.getByText('Enter at least 2 characters to search.')).toBeVisible()
    expect(requests).toBe(0)
  })

  test('distinguishes an empty result from an API failure', async ({ page }) => {
    await page.route('**/api/products/search**', route => route.fulfill({ json: [] }))
    await page.goto('/products/search?q=missing')
    await expect(page.getByRole('heading', { name: 'No matching products' })).toBeVisible()

    await page.route('**/api/products/search**', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }))
    await page.goto('/products/search?q=unavailable')
    await expect(page.getByRole('heading', { name: 'We couldn’t load your results' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
  })
})
