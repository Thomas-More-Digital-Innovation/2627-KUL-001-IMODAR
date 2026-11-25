<script lang="ts">
  import type { Snippet } from 'svelte';
  let { children }: { children?: Snippet } = $props();
</script>

<p class="notice" role="note">
  {#if children}{@render children()}{:else}Preview with sample data. Saving is not connected yet.{/if}
</p>
