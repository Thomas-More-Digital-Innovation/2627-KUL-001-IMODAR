import type { Page } from '@playwright/test';
import type { CurrentUser } from '../src/lib/api/auth';

export async function signIn(page: Page, role: CurrentUser['role'] = 'admin'): Promise<void> {
  const json: CurrentUser = { email: 'ada@example.com', full_name: 'Ada', role };
  await page.route('**/api/auth/me', (route) => route.fulfill({ json }));
}
