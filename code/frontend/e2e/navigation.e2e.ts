import { expect, test } from '@playwright/test';

test('login states that sign-in is not connected', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email address').fill('a@example.com');
  await page.getByLabel('Password').fill('not-a-real-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('status')).toContainText('not connected');
});

test('user menu leads to settings', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Researcher/ }).click();
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
