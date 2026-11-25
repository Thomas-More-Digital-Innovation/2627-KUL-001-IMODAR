<script lang="ts">
  import type { AnalysisResponse } from '#lib/api/client.ts';
  import Card from './Card.svelte';
  import Graphs from './Graphs.svelte';
  import Markdown from './Markdown.svelte';
  import { downloadCsv } from '#lib/csv.ts';
  let { result }: { result: AnalysisResponse } = $props();
  const label = 'text-[12.7px] tracking-[0.6px] text-muted uppercase';
  const stats = $derived(
    result.table
      ? [
          ['Total rows', result.table.row_count],
          ['Execution time', `${result.table.elapsed_ms.toFixed(1)} ms`],
          ['Columns', result.table.columns.length],
        ]
      : [],
  );
  const heading = $derived(
    { ok: 'Answer', clarify: 'Clarification needed', error: 'Analysis failed' }[result.status],
  );
</script>

<p
  class="max-w-[713px] self-end rounded-[17px] rounded-tr-[4px] bg-brand px-[21px] py-[17px] leading-[25px] wrap-anywhere text-white"
>
  {result.question}
</p>
<Card as="article" class="rounded-2xl shadow-[0_8px_34px_#143e4512]">
  <header class="border-b border-[#e6eded] px-[30px] py-[9px] text-[12.7px] text-muted">
    {result.table ? `Generated from ${result.table.row_count} rows` : 'No tabular data returned'}
  </header>
  <div class="p-[30px]">
    <h2 class="text-[21px]">{heading}</h2>
    <div data-testid="summary" class="mt-2 text-[#5e7479]">
      <Markdown source={result.summary} />
    </div>
    {#if result.table}
      {@const table = result.table}
      <dl class="my-[25px] grid grid-cols-3 gap-[13px]">
        {#each stats as [name, value] (name)}
          <div class="rounded-[13px] bg-surface p-[17px]">
            <dt class={label}>{name}</dt>
            <dd class="mt-2 text-[25px]">{value}</dd>
          </div>
        {/each}
      </dl>
      <div class="max-h-[480px] overflow-auto rounded-[13px] border border-[#dfe8e9]">
        <table class="w-full border-collapse">
          <thead class="bg-[#f5f8f8]">
            <tr>
              {#each table.columns as column, index (index)}<th
                  class={[label, 'px-[17px] py-[13px] text-left font-normal']}
                >
                  {column}
                </th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each table.rows as row, index (index)}
              <tr>
                {#each row as value, column (column)}<td
                    class="border-t border-[#e7eeee] px-[17px] py-[13px] text-[14.8px]"
                  >
                    {value ?? '–'}
                  </td>{/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if table.truncated}<p class="mt-2">Showing the first {table.rows.length} rows.</p>{/if}
      <button
        class="flex items-center gap-2 pt-[25px] text-action"
        onclick={() => downloadCsv('query_results.csv', table.columns, table.rows)}
      >
        <img src="/images/download.svg" alt="" /> Download CSV
      </button>
    {/if}
    {#if result.graphs}
      <Graphs
        report={result.graphs}
        truncatedTo={result.table?.truncated ? result.table.rows.length : null}
      />
    {/if}
    <details class="mt-[25px]">
      <summary class="cursor-pointer text-brand">Audit trail</summary>
      <h3 class="mt-4 mb-1.5 text-[16px]">Plan</h3>
      <Markdown source={result.audit.reasoning} />
      <p>
        Sources: {result.audit.data_sources.join(', ') || 'None'} · Attempts: {result.audit
          .attempts}
      </p>
      {#if result.audit.entities.length}
        <h3 class="mt-4 mb-1.5 text-[16px]">Resolved entities</h3>
        <ul class="my-3.5 list-disc pl-10">
          {#each result.audit.entities as entity, index (index)}
            <li>
              {entity.mention} → {entity.resolved_to} ({entity.domain}, {entity.score.toFixed(1)}%, {entity.source})
            </li>
          {/each}
        </ul>
      {/if}
      {#if result.audit.checks.length}
        <h3 class="mt-4 mb-1.5 text-[16px]">Guardrail</h3>
        <ul class="my-3.5 list-disc pl-10">
          {#each result.audit.checks as check (check.name)}
            <li>{check.passed ? 'Pass' : 'Fail'} · {check.name}: {check.detail}</li>
          {/each}
        </ul>
      {/if}
      {#if result.audit.sql}<h3 class="mt-4 mb-1.5 text-[16px]">SQL</h3>
        <pre class="my-[13px] overflow-x-auto rounded-xl bg-[#f5f8f8] p-4 text-[13px]">{result.audit
            .sql}</pre>{/if}
    </details>
  </div>
</Card>
