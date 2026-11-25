<script lang="ts">
  let { name, class: extra }: { name: string; class?: string } = $props();
</script>

<span
  class={['bg-current mask-contain mask-center mask-no-repeat', extra]}
  style:mask-image={`url(/images/${name}.svg)`}
></span>
