<script lang="ts">
  import type { Snippet } from 'svelte';
  let { title, children }: { title: string; children?: Snippet } = $props();
</script>

<div class="flex flex-wrap items-center gap-4">
  <h1 class="flex-1 text-[34px] font-bold text-[#183b44]">{title}</h1>
  {@render children?.()}
</div>
