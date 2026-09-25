import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './ux-tests',
  testMatch: '**/*.e2e.ts',
  outputDir: './test-results/ux',
  workers: 1,
  timeout: 45000,
  use: { baseURL: 'http://localhost:4010', channel: 'msedge', headless: true, trace: 'retain-on-failure' },
  webServer: {
    command: process.env.UX_PRODUCTION === '1'
      ? 'node node_modules/next/dist/bin/next start -p 4010'
      : 'node node_modules/next/dist/bin/next dev -p 4010',
    url: 'http://localhost:4010/products/search',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
