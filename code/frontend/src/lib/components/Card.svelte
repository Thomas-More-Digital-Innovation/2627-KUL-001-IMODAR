<script lang="ts">
  import type { HTMLAttributes } from 'svelte/elements';
  let {
    as = 'section',
    class: extra,
    children,
    ...rest
  }: HTMLAttributes<HTMLElement> & { as?: 'section' | 'article' } = $props();
</script>

<svelte:element this={as} class={['border border-line bg-white', extra]} {...rest}>
  {@render children?.()}
</svelte:element>
