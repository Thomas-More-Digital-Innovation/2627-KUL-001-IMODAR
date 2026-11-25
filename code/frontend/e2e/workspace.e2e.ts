import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { signIn } from './sign-in';
import type { AnalysisResponse } from '../src/lib/api/client';

const answer: AnalysisResponse = {
  question: 'Compare CRP',
  status: 'ok',
  summary: 'Cases are higher.',
  elapsed_ms: 20,
  table: {
    columns: ['cohort', 'mean'],
    rows: [['Case', 16.42]],
    row_count: 1,
    truncated: false,
    elapsed_ms: 2,
  },
  audit: {
    reasoning: 'Average per cohort',
    data_sources: ['omop.measurement'],
    sql: 'SELECT 1',
    entities: [],
    checks: [{ name: 'syntax', passed: true, detail: 'one SELECT' }],
    attempts: 1,
  },
};

test.beforeEach(({ page }) => signIn(page));

test('asks a question, audits it and downloads the rows', async ({ page }) => {
  await page.route('**/api/analyses', (route) => route.fulfill({ json: answer }));
  await page.goto('/');
  await page.getByLabel('Ask a question').fill('Compare CRP');
  await page.getByRole('button', { name: 'Submit question' }).click();
  await expect(page.getByText('Cases are higher.')).toBeVisible();
  await expect(page.getByRole('cell', { name: '16.42' })).toBeVisible();
  await expect(page.getByLabel('Ask a question')).toHaveValue('');

  await page.getByText('Audit trail').click();
  await expect(page.getByText('SELECT 1')).toBeVisible();

  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download CSV' }).click();
  expect(await readFile(await (await download).path(), 'utf8')).toBe('cohort,mean\r\nCase,16.42');

  await page.getByRole('button', { name: '+ New analysis' }).click();
  await expect(page.getByText('Cases are higher.')).toBeHidden();
  await page.getByRole('navigation').getByRole('button', { name: 'Compare CRP' }).click();
  await expect(page.getByText('Cases are higher.')).toBeVisible();
});

test('renders markdown without trusting it and sends thinking mode', async ({ page }) => {
  let think: unknown;
  await page.route('**/api/analyses', (route) => {
    think = route.request().postDataJSON().think;
    const summary =
      '## Finding\n\n- **CRP** is `high`\n- second\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n' +
      '<img src=x onerror="window.hacked=1"> [click](javascript:alert(1))';
    return route.fulfill({ json: { ...answer, table: null, summary } });
  });
  await page.goto('/');
  const toggle = page.getByRole('button', { name: 'Thinking' });
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Ask a question').fill('Compare CRP');
  await page.getByRole('button', { name: 'Submit question' }).click();
  const summary = page.locator('.summary');
  await expect(summary.getByRole('heading', { name: 'Finding' })).toBeVisible();
  await expect(summary.getByRole('listitem')).toHaveCount(2);
  await expect(summary.locator('strong')).toHaveText('CRP');
  await expect(summary.getByRole('cell', { name: '2' })).toBeVisible();
  await expect(summary.locator('img, a')).toHaveCount(0);
  await expect(summary).toContainText('<img src=x');
  expect(think).toBe(true);
});

test('keeps the question when the API is unavailable', async ({ page }) => {
  // Not mocked: exercises the real proxy with no backend behind it.
  await page.goto('/');
  await page.getByLabel('Ask a question').fill('Compare CRP');
  await page.getByLabel('Ask a question').press('Enter');
  await expect(page.getByRole('alert')).toContainText('unavailable');
  await expect(page.getByLabel('Ask a question')).toHaveValue('Compare CRP');
});
