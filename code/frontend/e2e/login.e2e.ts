import { expect, test, type Page } from '@playwright/test';
import { signIn } from './sign-in';

async function submitPassword(page: Page, next: 'enrol' | 'verify') {
  await page.route('**/api/auth/login', (route) => route.fulfill({ json: { next } }));
  await page.goto('/login');
  await page.getByLabel('Email address').fill('ada@example.com');
  await page.getByLabel('Password').fill('synthetic-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('visitors are sent to login', async ({ page }) => {
  await page.route('**/api/auth/me', (route) => route.fulfill({ status: 401, json: {} }));
  await page.goto('/admin/users');
  await expect(page).toHaveURL('/login');
});

test('a wrong code is reported and a correct one signs in', async ({ page }) => {
  await submitPassword(page, 'verify');
  await page.route('**/api/auth/2fa/verify', (route) =>
    route.request().postDataJSON().code === '123456'
      ? route.fulfill({ status: 204 })
      : route.fulfill({ status: 401, json: { detail: 'The code is incorrect.' } }),
  );
  const code = page.getByLabel('Authenticator or recovery code');
  await code.fill('000000');
  await page.getByRole('button', { name: 'Verify' }).click();
  await expect(page.getByRole('alert')).toContainText('incorrect');
  await signIn(page);
  await code.fill('123456');
  await page.getByRole('button', { name: 'Verify' }).click();
  await expect(page).toHaveURL('/');
});

test('first sign-in sets up 2FA and shows recovery codes', async ({ page }) => {
  await page.route('**/api/auth/2fa/enrol', (route) =>
    route.fulfill({ json: { secret: 'SYNTHETIC', qr_code: 'data:image/svg+xml,<svg/>' } }),
  );
  await page.route('**/api/auth/2fa/confirm', (route) =>
    route.fulfill({ json: { recovery_codes: ['first-code', 'second-code'] } }),
  );
  await submitPassword(page, 'enrol');
  await expect(page.getByText('SYNTHETIC')).toBeVisible();
  await page.getByLabel('Authenticator code').fill('123456');
  await page.getByRole('button', { name: 'Verify' }).click();
  await expect(page.getByText('second-code')).toBeVisible();
  await signIn(page);
  await page.getByRole('button', { name: 'I saved these codes' }).click();
  await expect(page).toHaveURL('/');
});
