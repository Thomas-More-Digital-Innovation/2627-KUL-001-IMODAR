<script lang="ts">
  import type { Snippet } from 'svelte';
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

<dialog bind:this={element} onclose={() => (open = false)} aria-label={title}>
  <header>
    <h2>{title}</h2>
    <button aria-label="Close" onclick={() => (open = false)}>×</button>
  </header>
  <div class="content">{@render children()}</div>
  <footer>
    <button class="btn" onclick={() => (open = false)}>Cancel</button>{@render actions()}
  </footer>
</dialog>

<style>
  dialog {
    width: min(640px, 94vw);
    padding: 0;
    border: 0;
    border-radius: 16px;
    color: #294952;
    font-family: var(--admin);
    box-shadow: 0 16px 64px #122e372e;
  }
  dialog::backdrop {
    background: #16363d73;
  }
  header {
    display: flex;
    justify-content: space-between;
    padding: 26px 32px 8px;
    font-size: 28px;
  }
  h2 {
    font-weight: 700;
  }
  .content {
    display: grid;
    gap: 20px;
    padding: 8px 32px 24px;
  }
  footer {
    display: flex;
    justify-content: flex-end;
    gap: 16px;
    padding: 28px 32px;
    background: #f8fafb;
  }
</style>
