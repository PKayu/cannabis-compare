import { expect, test } from '@playwright/test'
import { bypassAgeGate, mockEmptyApi } from './helpers'

test.describe('Shared public shell', () => {
  test.beforeEach(async ({ page }) => {
    await bypassAgeGate(page)
    await mockEmptyApi(page)
  })

  test('loads the approved brand, main landmark, and compliance notice', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('link', { name: 'Mountain Bloom home' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Find your next stop.' })).toBeVisible()
    await expect(page.getByRole('main')).toHaveCount(1)
    await expect(page.getByRole('complementary', { name: 'Important site information' })).toBeVisible()
    await expect(page.getByText(/does not sell controlled substances/i)).toBeVisible()
  })

  test('keeps primary navigation usable at desktop and mobile widths', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto('/')
    const desktopNav = page.getByRole('navigation', { name: 'Primary' })
    await expect(desktopNav.getByRole('link', { name: 'Discover' })).toBeVisible()
    await expect(desktopNav.getByRole('link', { name: 'Dispensaries' })).toBeVisible()

    await page.setViewportSize({ width: 390, height: 844 })
    await page.getByRole('button', { name: 'Menu' }).click()
    const mobileNav = page.getByRole('navigation', { name: 'Mobile primary' })
    await expect(mobileNav.getByRole('link', { name: 'Discover' })).toBeVisible()
    await mobileNav.getByRole('link', { name: 'Discover' }).focus()
    await page.keyboard.press('Escape')
    await expect(page.getByRole('button', { name: 'Menu' })).toBeFocused()
  })

  test('keeps the shared compliance treatment on task and legal routes', async ({ page }) => {
    for (const path of ['/products/search', '/dispensaries', '/terms', '/privacy']) {
      await page.goto(path)
      await expect(page.getByRole('main')).toHaveCount(1)
      await expect(page.getByRole('complementary', { name: 'Important site information' })).toBeVisible()
    }
  })

  test('returns a real not-found response for an unknown route', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist')
    expect(response?.status()).toBe(404)
    await expect(page.getByRole('heading', { name: 'This page could not be found.' })).toBeVisible()
  })
})
