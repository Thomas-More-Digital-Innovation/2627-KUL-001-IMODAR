<script lang="ts">
  import type { Snippet } from 'svelte';
  let { role, children }: { role: 'note' | 'status' | 'alert'; children: Snippet } = $props();
</script>

<p {role} class="rounded-lg bg-warning-tint px-4 py-2.5 text-warning">{@render children()}</p>
