import { defineConfig } from '@playwright/test'

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:4010'
const externalServer = process.env.E2E_EXTERNAL_SERVER === '1'

export default defineConfig({
  testDir: './ux-tests',
  testMatch: '**/*.e2e.ts',
  outputDir: './test-results/ux',
  workers: 1,
  timeout: 45000,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['html', { outputFolder: './playwright-report/ux', open: 'never' }],
    ['json', { outputFile: './playwright-report/ux-results.json' }],
    ['junit', { outputFile: './playwright-report/ux-results.xml' }],
    ['list'],
  ],
  use: {
    baseURL,
    browserName: 'chromium',
    channel: process.env.CI ? undefined : 'msedge',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: externalServer ? undefined : {
    command: process.env.UX_PRODUCTION === '1'
      ? 'node node_modules/next/dist/bin/next start -p 4010'
      : 'node node_modules/next/dist/bin/next dev -p 4010',
    url: `${baseURL}/products/search`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: {
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://test.supabase.co',
      NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'test-anon-key',
    },
  },
})
