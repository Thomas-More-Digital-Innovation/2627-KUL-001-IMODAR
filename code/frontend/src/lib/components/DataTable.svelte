<script lang="ts">
  import type { Snippet } from 'svelte';
  import Card from './Card.svelte';
  let { columns, summary, children }: { columns: string[]; summary: string; children: Snippet } =
    $props();
  const head = 'bg-[#f8fafb] px-3 py-4 text-left text-[13px] font-bold text-[#637d85]';
</script>

<Card class="overflow-x-auto rounded-xl shadow-[0_1px_3px_#0000001a]">
  <table
    class="w-full border-collapse [&_td]:border-b [&_td]:border-[#e6edef] [&_td]:px-3 [&_td]:py-2.5 [&_td_select]:min-h-11 [&_td_select]:rounded-lg [&_td_select]:border [&_td_select]:border-[#d3e0e4] [&_td_select]:bg-white [&_td_select]:px-3.5 [&_td_small]:mt-1 [&_td_small]:block [&_td_small]:text-[12px] [&_td_small]:font-normal [&_td_small]:text-[#637d85] [&_tr:has(td_input:checked)]:bg-[#f4fafb]"
  >
    <thead>
      <tr>
        <th class={head}><span class="sr-only">Select</span></th>
        {#each columns as column (column)}<th class={head}>{column}</th>{/each}
      </tr>
    </thead>
    <tbody>{@render children()}</tbody>
  </table>
  <p class="px-6 py-4 text-[13px] text-[#637d85]">{summary}</p>
</Card>
