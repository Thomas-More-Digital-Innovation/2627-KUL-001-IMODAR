<script lang="ts">
  import type { Snippet } from 'svelte';
  import Button from './Button.svelte';
  let {
    title,
    open = $bindable(false),
    children,
    actions,
  }: { title: string; open: boolean; children: Snippet; actions: Snippet } = $props();
  let element: HTMLDialogElement;
  $effect(() => {
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  });
</script>

<dialog
  class="m-auto w-[min(640px,94vw)] rounded-2xl bg-white font-admin text-[#294952] shadow-[0_16px_64px_#122e372e] backdrop:bg-[#16363d73]"
  bind:this={element}
  onclose={() => (open = false)}
  aria-label={title}
>
  <header class="flex justify-between px-8 pt-[26px] pb-2 text-[28px]">
    <h2 class="font-bold">{title}</h2>
    <button class="px-1.5 py-px" aria-label="Close" onclick={() => (open = false)}>×</button>
  </header>
  <div class="grid gap-5 px-8 pt-2 pb-6">{@render children()}</div>
  <footer class="flex justify-end gap-4 bg-[#f8fafb] px-8 py-7">
    <Button onclick={() => (open = false)}>Cancel</Button>{@render actions()}
  </footer>
</dialog>
