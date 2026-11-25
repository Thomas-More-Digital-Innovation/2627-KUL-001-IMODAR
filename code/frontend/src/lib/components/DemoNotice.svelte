<script lang="ts">
  import type { Snippet } from 'svelte';
  import Notice from './Notice.svelte';
  let { children }: { children?: Snippet } = $props();
</script>

<Notice role="note">
  {#if children}{@render children()}{:else}Preview with sample data. Saving is not connected yet.{/if}
</Notice>
