import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  testMatch: '**/*.e2e.ts',
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4173',
    // An unreachable API, so a running dev server cannot influence the tests.
    env: { BACKEND_URL: 'http://127.0.0.1:9' },
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
  },
});
