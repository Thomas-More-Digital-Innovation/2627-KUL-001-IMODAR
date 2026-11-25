<script lang="ts">
  import { lexer } from 'marked';
  import MarkdownTokens from './MarkdownTokens.svelte';
  let { source }: { source: string } = $props();
  const tokens = $derived(lexer(source, { gfm: true }));
</script>

<div class="markdown"><MarkdownTokens {tokens} /></div>

<style>
  .markdown {
    line-height: 25px;
    overflow-wrap: anywhere;
  }
  .markdown :global(:is(p, ul, ol, pre, blockquote, .table)) {
    margin: 0 0 12px;
  }
  .markdown :global(:is(h3, h4, h5)) {
    margin: 16px 0 8px;
    color: var(--ink);
    font-size: 17px;
    font-weight: 800;
  }
  .markdown :global(strong) {
    color: var(--ink);
    font-weight: 800;
  }
  .markdown :global(code) {
    padding: 2px 5px;
    border-radius: 4px;
    background: #f1f8f8;
  }
  .markdown :global(pre) {
    padding: 16px;
    border-radius: 12px;
    background: #f1f8f8;
    overflow-x: auto;
  }
  .markdown :global(blockquote) {
    padding-left: 16px;
    border-left: 3px solid var(--border);
  }
  .markdown :global(.table) {
    overflow-x: auto;
  }
  .markdown :global(table) {
    border-collapse: collapse;
  }
  .markdown :global(:is(th, td)) {
    padding: 6px 14px;
    border: 1px solid var(--border);
    text-align: left;
  }
</style>
