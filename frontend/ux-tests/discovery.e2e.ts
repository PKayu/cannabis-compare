import { test, expect, type Page } from '@playwright/test'
import { product, groups, results } from './fixtures'

async function mockApi(page: Page) {
  await page.addInitScript(() => localStorage.setItem('age_verified', 'true'))
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname
    let data: unknown = []
    if (path === '/api/products/search') data = results
    else if (path === '/api/products/autocomplete') data = [{ id: 'master', name: 'Blue Dream', brand: 'Example Grower', type: 'flower' }]
    else if (path.endsWith('/prices')) data = groups
    else if (path.endsWith('/pricing-history')) data = [{ date: '2026-09-22', min: 30, max: 60, avg: 45 }, { date: '2026-09-25', min: 32, max: 60, avg: 46 }]
    else if (path === '/api/products/master') data = product
    await route.fulfill({ json: data })
  })
}
test.beforeEach(async ({ page }) => { await mockApi(page) })

async function readyForScreenshot(page: Page) {
  for (const image of await page.locator('img').all()) {
    await image.scrollIntoViewIfNeeded()
    await expect(image).toHaveJSProperty('complete', true)
    expect(await image.evaluate(node => (node as HTMLImageElement).naturalWidth)).toBeGreaterThan(0)
  }
  await page.evaluate(async () => { await document.fonts.ready; window.scrollTo({ top: 0, behavior: 'instant' }) })
}

for (const width of [390, 768, 1280, 1440]) {
  test(`homepage search and layout at ${width}px`, async ({ page }, info) => {
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Find your next stop.' })).toBeVisible()
    await expect(page.getByRole('link', { name: /Browse dispensaries/ })).toHaveAttribute('href', '/dispensaries')
    await expect(page.getByRole('main')).toHaveCount(1)
    await expect(page.getByRole('complementary', { name: 'Important site information' })).toBeVisible()
    await expect(page.getByRole('link', { name: /Guidance/ })).toHaveCount(0)
    const search = page.getByRole('combobox', { name: 'Search products or brands' })
    await search.fill('b')
    await page.getByRole('button', { name: 'Search', exact: true }).click()
    await expect(page.getByText('Enter at least 2 characters to search.', { exact: true })).toBeVisible()
    await search.fill('blue')
    await expect(page.getByRole('option', { name: /Blue Dream/ })).toBeVisible()
    await search.press('ArrowDown')
    await search.press('Enter')
    await expect(page).toHaveURL('/products/search?q=Blue%20Dream')
    await page.goBack()
    await readyForScreenshot(page)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: info.outputPath(`home-${width}.png`), fullPage: true })
    expect(errors).toEqual([])
  })
}

for (const width of [390, 768, 1280, 1440]) {
  test(`discovery and comparison at ${width}px`, async ({ page }, info) => {
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/products/search?q=blue&max_price=70')
    await expect(page.getByRole('combobox', { name: 'Search products or brands' })).toHaveValue('blue')
    await expect(page.getByText('2 products found')).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await readyForScreenshot(page)
    await page.screenshot({ path: info.outputPath(`search-${width}.png`), fullPage: true })
    await page.getByRole('link', { name: 'Blue Dream', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Blue Dream', exact: true })).toBeVisible()
    await expect(page.getByText('Unknown Size Dispensary')).toHaveCount(0)
    await expect(page.getByRole('link', { name: /View at dispensary/ })).toHaveAttribute('href', 'https://example.com/product/blue-dream')
    await page.getByRole('radio', { name: '7g', exact: true }).check()
    await expect(page.getByRole('link', { name: /Visit dispensary website/ })).toHaveAttribute('href', 'https://example.com/')
    await page.getByRole('radio', { name: 'Size not reported' }).check()
    await expect(page.getByText('No dispensary link available.')).toBeVisible()
    await page.getByRole('radio', { name: '14g', exact: true }).check()
    await expect(page.getByText('No current prices for this package')).toBeVisible()
    await page.getByRole('radio', { name: '3.5g', exact: true }).check()
    await expect(page.getByText('No reviews yet.', { exact: false })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await readyForScreenshot(page)
    await page.screenshot({ path: info.outputPath(`product-${width}.png`), fullPage: true })
    await page.getByRole('link', { name: 'Back to discovery' }).first().click()
    await expect(page).toHaveURL(/q=blue&max_price=70/)
    expect(errors).toEqual([])
  })
}
test('search failure is distinct from empty results and retries preserve filters', async ({ page }) => {
  let failing = true
  await page.route('**/api/products/search?**', route => route.fulfill(failing ? { status: 503, json: { detail: 'Unavailable' } } : { json: [] }))
  await page.goto('/products/search?q=blue&min_thc=20')
  await expect(page.getByRole('heading', { name: 'We couldn’t load your results' })).toBeVisible()
  failing = false
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'No matching products' })).toBeVisible()
  await expect(page).toHaveURL(/min_thc=20/)
})
test('price failure leaves product available, with working retry', async ({ page }) => {
  let failing = true
  await page.route('**/api/products/master/prices', route => route.fulfill(failing ? { status: 503, json: {} } : { json: groups }))
  await page.goto('/products/master')
  await expect(page.getByRole('heading', { name: 'Blue Dream', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Retry offers' })).toBeVisible()
  failing = false
  await page.getByRole('button', { name: 'Retry offers' }).click()
  await expect(page.getByRole('radio', { name: '3.5g', exact: true })).toBeVisible()
})
test('keyboard search, package selection, mobile menu and signed-out save', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/products/search')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused()
  await page.keyboard.press('Enter')
  const input = page.getByRole('combobox', { name: 'Search products or brands' })
  await input.focus()
  await input.fill('blue')
  await expect(page.getByRole('option', { name: /Blue Dream/ })).toBeVisible()
  await input.press('ArrowDown')
  await input.press('Enter')
  await expect(page.getByText('2 products found')).toBeVisible()
  const result = page.getByRole('link', { name: 'Blue Dream', exact: true })
  await result.focus(); await page.keyboard.press('Enter')
  const first = page.getByRole('radio', { name: '3.5g', exact: true })
  await first.focus(); await page.keyboard.press('ArrowRight')
  await expect(page.getByRole('radio', { name: '7g', exact: true })).toBeChecked()
  await page.getByRole('button', { name: 'Menu', exact: true }).click()
  await page.getByRole('navigation', { name: 'Mobile primary' }).getByRole('link', { name: 'Discover' }).focus()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'Menu', exact: true })).toBeFocused()
  await page.getByRole('button', { name: 'Save product' }).click()
  await expect(page).toHaveURL(/auth\/login\?returnUrl=/)
  const returnTo = new URL(page.url()).searchParams.get('returnUrl')
  expect(returnTo).toContain('/products/master?returnTo=')
})

test('filters send supported values, validate ranges, and survive browser back', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/products/search?q=blue')
  await page.getByRole('button', { name: 'Tune the menu' }).click()
  await page.getByRole('combobox', { name: 'Product type', exact: true }).selectOption('flower')
  await page.getByRole('spinbutton', { name: 'Minimum price', exact: true }).fill('60')
  await page.getByRole('spinbutton', { name: 'Maximum price', exact: true }).fill('40')
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await expect(page.getByText('Price minimum must not exceed its maximum.')).toBeVisible()
  await page.getByRole('spinbutton', { name: 'Minimum price', exact: true }).fill('20')
  await page.getByRole('spinbutton', { name: 'Minimum THC', exact: true }).fill('15')
  await page.getByRole('combobox', { name: 'Sort results' }).selectOption('price_low')
  const request = page.waitForRequest(request => request.url().includes('/api/products/search?') && request.url().includes('min_price=20'))
  await page.getByRole('button', { name: 'Apply filters' }).click()
  const params = new URL((await request).url()).searchParams
  expect(Object.fromEntries(params)).toMatchObject({ q: 'blue', product_type: 'flower', min_price: '20', max_price: '40', min_thc: '15', sort_by: 'price_low' })
  await page.goBack()
  await expect(page.getByRole('spinbutton', { name: 'Minimum price', exact: true })).toHaveValue('')
})
test('loading, missing product, optional failures and review authentication are explicit', async ({ page }) => {
  let release: () => void = () => {}
  const hold = new Promise<void>(resolve => { release = resolve })
  await page.route('**/api/products/search?**', async route => { await hold; await route.fulfill({ json: results }) })
  await page.goto('/products/search?q=blue')
  await expect(page.getByRole('heading', { name: 'Gathering prices…' })).toBeVisible()
  release()
  await expect(page.getByText('2 products found')).toBeVisible()
  await page.route('**/api/products/missing', route => route.fulfill({ status: 404, json: {} }))
  await page.goto('/products/missing')
  await expect(page.getByRole('heading', { name: 'This product could not be found' })).toBeVisible()
  await page.route('**/api/reviews/product/master?**', route => route.fulfill({ status: 503, json: {} }))
  await page.route('**/api/products/master/pricing-history?**', route => route.fulfill({ status: 503, json: {} }))
  await page.goto('/products/master')
  await expect(page.getByRole('button', { name: 'Retry reviews' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Retry price observations' })).toBeVisible()
  await page.getByRole('button', { name: 'Write a review' }).click()
  await expect(page.getByText('Please sign in to leave a review.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Submit Review' })).toHaveCount(0)
})

test('shared shell preserves one main landmark on home and legal routes', async ({ page }) => {
  for (const path of ['/', '/terms', '/privacy']) {
    await page.goto(path)
    await expect(page.getByRole('main')).toHaveCount(1)
    await expect(page.getByRole('link', { name: 'Mountain Bloom home' })).toBeVisible()
    await expect(page.getByRole('complementary', { name: 'Important site information' })).toBeVisible()
    await expect(page.getByRole('link', { name: /Guidance/ })).toHaveCount(0)
  }
})
