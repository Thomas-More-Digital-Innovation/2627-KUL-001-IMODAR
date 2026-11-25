<script lang="ts">
  import type { Snippet } from 'svelte';
  let {
    label,
    hint,
    large = false,
    class: extra,
    children,
  }: {
    label: string;
    hint?: string;
    large?: boolean;
    class?: string;
    children: Snippet;
  } = $props();
  const control =
    '[&_:is(input,select)]:w-full [&_:is(input,select)]:border [&_:is(input,select)]:border-field [&_:is(input,select)]:bg-white';
  const sizes = {
    normal:
      'text-[14px] [&_:is(input,select)]:h-12 [&_:is(input,select)]:rounded-xl [&_:is(input,select)]:px-4 [&_:is(input,select)]:text-[16px]',
    large:
      'text-[19.3px] [&_input]:h-[77px] [&_input]:rounded-[16.5px] [&_input]:px-[21px] [&_input]:text-[22px]',
  };
</script>

<label class={['grid gap-2', control, large ? sizes.large : sizes.normal, extra]}>
  {label}
  {#if hint}<small class="text-[12px]">{hint}</small>{/if}
  {@render children()}
</label>
