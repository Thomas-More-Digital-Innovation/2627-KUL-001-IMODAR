import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';

export default ts.config(
  {
    ignores: [
      '.svelte-kit/',
      'build/',
      'test-results/',
      'playwright-report/',
      'src/lib/api/schema.ts',
    ],
  },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...svelte.configs.recommended,
  { languageOptions: { globals: { ...globals.browser, ...globals.node } } },
  {
    files: ['**/*.svelte', '**/*.svelte.ts'],
    languageOptions: { parserOptions: { parser: ts.parser } },
    // The app is served from the domain root, so links need no base-path resolution.
    rules: { 'svelte/no-navigation-without-resolve': 'off' },
  },
);
