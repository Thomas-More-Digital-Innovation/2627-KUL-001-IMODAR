<script lang="ts">
  let { status }: { status: string } = $props();
  const tones: Record<string, string> = {
    Invited: 'bg-warning-tint text-warning',
    Draft: 'bg-warning-tint text-warning',
    Suspended: 'bg-[#fbecec] text-[#9c4545]',
    Archived: 'bg-[#e9eef1] text-[#576f77]',
  };
</script>

<span
  class={[
    'inline-block rounded-[14px] px-5 py-[5px] text-[12px] font-semibold',
    tones[status] ?? 'bg-[#e6f3ec] text-[#2e6d50]',
  ]}
>
  {status}
</span>
