<script lang="ts">
  import type { Snippet } from 'svelte';
  let { children }: { children: Snippet } = $props();
</script>

<div
  class="flex flex-wrap items-center gap-4 *:min-h-11 *:rounded-lg *:border *:border-[#d3e0e4] *:bg-white *:px-3.5 [&>input]:min-w-[200px] [&>input]:flex-1"
>
  {@render children()}
</div>
