import { expect, test } from '@playwright/test';
import { signIn } from './sign-in';

test.beforeEach(({ page }) => signIn(page));

test('user menu leads to settings', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Ada/ }).click();
  await page.getByRole('link', { name: 'Settings' }).click();
  await expect(page.getByRole('heading', { name: 'Profile information' })).toBeVisible();
  await page.getByRole('link', { name: 'Security' }).click();
  await expect(page.getByRole('heading', { name: 'Active sessions' })).toBeVisible();
});

test('admin filters users and opens the edit dialog', async ({ page }) => {
  await page.goto('/admin/users');
  await page.getByLabel('Filter by status').selectOption('Suspended');
  await expect(page.getByText('Showing 1 of 4 users')).toBeVisible();
  await page.getByRole('button', { name: 'Edit' }).click();
  const dialog = page.getByRole('dialog', { name: 'Edit user' });
  await expect(dialog.getByLabel('Email address')).toHaveValue('john.doe4@example.com');
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
});

test('admin confirms bulk deletion and reaches resource access', async ({ page }) => {
  await page.goto('/admin/case-studies');
  await page.getByLabel('Select Community health outcomes').check();
  await page.getByLabel('Select Remote care adoption').check();
  await page.locator('.bulk').getByRole('button', { name: 'Delete' }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete 2 papers?' });
  await expect(dialog.getByRole('listitem')).toHaveCount(2);
  await dialog.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('link', { name: 'Resource access' }).click();
  await expect(page.getByRole('heading', { name: 'Users & Resources access' })).toBeVisible();
});

test('researchers cannot open the dashboard', async ({ page }) => {
  await signIn(page, 'researcher');
  await page.goto('/admin/users');
  await expect(page).toHaveURL('/');
  await page.getByRole('button', { name: /Ada/ }).click();
  await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Dashboard' })).toBeHidden();
});

test('password confirmation must match before anything is sent', async ({ page }) => {
  let sent = false;
  await page.route('**/api/auth/password', (route) => {
    sent = true;
    return route.fulfill({ status: 204 });
  });
  await page.goto('/settings/security');
  await page.getByLabel('Current password').fill('synthetic-current');
  await page.getByLabel('New password').fill('synthetic-new-password');
  await page.getByLabel('Confirm password').fill('something-else');
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page.getByRole('alert')).toContainText('do not match');
  expect(sent).toBe(false);
  await page.getByLabel('Confirm password').fill('synthetic-new-password');
  await page.getByRole('button', { name: 'Update password' }).click();
  await expect(page.getByRole('status')).toContainText('Password updated');
});
