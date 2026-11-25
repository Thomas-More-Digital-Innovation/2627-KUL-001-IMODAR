<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';
  let {
    pressed = $bindable(false),
    children,
    ...rest
  }: HTMLButtonAttributes & { pressed: boolean } = $props();
</script>

<button
  type="button"
  class="rounded-xl border border-field px-3.5 text-body aria-pressed:border-brand aria-pressed:bg-tint aria-pressed:text-brand"
  aria-pressed={pressed}
  onclick={() => (pressed = !pressed)}
  {...rest}
>
  {@render children?.()}
</button>
