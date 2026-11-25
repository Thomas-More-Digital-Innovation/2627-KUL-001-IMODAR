<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';
  type Variant = 'secondary' | 'primary' | 'danger' | 'danger-outline' | 'link' | 'danger-link';
  let {
    variant = 'secondary',
    class: extra,
    children,
    ...rest
  }: HTMLButtonAttributes & { variant?: Variant } = $props();
  const box = 'min-h-11 rounded-lg border px-5 font-semibold';
  const variants: Record<Variant, string> = {
    secondary: `${box} border-[#d7e2e6] bg-white`,
    primary: `${box} border-action bg-action text-white`,
    danger: `${box} border-danger bg-danger text-white`,
    'danger-outline': `${box} border-[#e0b9b9] bg-white text-danger`,
    link: 'px-1.5 py-px font-semibold text-brand',
    'danger-link': 'px-1.5 py-px font-semibold text-danger',
  };
</script>

<button class={[variants[variant], extra]} {...rest}>{@render children?.()}</button>
