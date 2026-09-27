import type { Page } from '@playwright/test'

export async function bypassAgeGate(page: Page) {
  await page.addInitScript(() => localStorage.setItem('age_verified', 'true'))
}

export async function mockEmptyApi(page: Page) {
  await page.route('**/api/**', route => route.fulfill({ json: [] }))
}
