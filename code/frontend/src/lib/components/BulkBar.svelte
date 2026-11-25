<script lang="ts">
  import type { Snippet } from 'svelte';
  let { count, onclear, children }: { count: number; onclear: () => void; children: Snippet } =
    $props();
</script>

{#if count}
  <div
    data-testid="bulk-actions"
    class="flex min-h-[46px] flex-wrap items-center gap-4 rounded-lg bg-tint px-4"
  >
    <strong>{count} selected</strong>
    {@render children()}
    <button class="px-1.5 py-px" onclick={onclear}>Clear selection</button>
  </div>
{/if}
