import { expect, test } from '@playwright/test'

test.describe('Age gate', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => localStorage.removeItem('age_verified'))
    await page.reload()
  })

  test('shows the supported confirmation choices and compliance notice', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Welcome!' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'I am 21 or older — Enter' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'I am under 21 — Exit' })).toBeVisible()
    await expect(page.getByText(/informational purposes only/i)).toBeVisible()
    await expect(page.getByText(/does not sell, distribute, or promote controlled substances/i)).toBeVisible()
  })

  test('persists an adult confirmation across a reload', async ({ page }) => {
    await page.getByRole('button', { name: 'I am 21 or older — Enter' }).click()

    await expect(page.getByRole('heading', { name: 'Find your next stop.' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Welcome!' })).toHaveCount(0)
    await expect.poll(() => page.evaluate(() => localStorage.getItem('age_verified'))).toBe('true')

    await page.reload()
    await expect(page.getByRole('heading', { name: 'Find your next stop.' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Welcome!' })).toHaveCount(0)
  })

  test('keeps both choices keyboard reachable', async ({ page }) => {
    const enter = page.getByRole('button', { name: 'I am 21 or older — Enter' })
    const exit = page.getByRole('button', { name: 'I am under 21 — Exit' })

    await enter.focus()
    await expect(enter).toBeFocused()
    await page.keyboard.press('Tab')
    await expect(exit).toBeFocused()
  })
})
