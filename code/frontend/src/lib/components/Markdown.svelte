<script lang="ts">
  import { lexer } from 'marked';
  import MarkdownTokens from './MarkdownTokens.svelte';
  let { source }: { source: string } = $props();
  const tokens = $derived(lexer(source, { gfm: true }));
</script>

<div class="leading-[25px] wrap-anywhere"><MarkdownTokens {tokens} /></div>
