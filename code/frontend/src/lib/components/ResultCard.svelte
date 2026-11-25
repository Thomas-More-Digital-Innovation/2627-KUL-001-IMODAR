<script lang="ts">
  import type { AnalysisResponse } from '#lib/api/client.ts';
  import { downloadCsv } from '#lib/csv.ts';
  let { result }: { result: AnalysisResponse } = $props();
  const heading = $derived(
    { ok: 'Answer', clarify: 'Clarification needed', error: 'Analysis failed' }[result.status],
  );
</script>

<p class="question">{result.question}</p>
<article class="card">
  <header>
    {result.table ? `Generated from ${result.table.row_count} rows` : 'No tabular data returned'}
  </header>
  <div class="content">
    <h2>{heading}</h2>
    <p class="summary">{result.summary}</p>
    {#if result.table}
      {@const table = result.table}
      <dl>
        <div>
          <dt>Total rows</dt>
          <dd>{table.row_count}</dd>
        </div>
        <div>
          <dt>Execution time</dt>
          <dd>{table.elapsed_ms.toFixed(1)} ms</dd>
        </div>
        <div>
          <dt>Columns</dt>
          <dd>{table.columns.length}</dd>
        </div>
      </dl>
      <div class="scroll">
        <table>
          <thead>
            <tr>
              {#each table.columns as column, index (index)}<th>{column}</th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each table.rows as row, index (index)}
              <tr>
                {#each row as value, column (column)}<td>{value ?? '–'}</td>{/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if table.truncated}<p class="note">Showing the first {table.rows.length} rows.</p>{/if}
      <button
        class="download"
        onclick={() => downloadCsv('query_results.csv', table.columns, table.rows)}
      >
        <img src="/images/download.svg" alt="" /> Download CSV
      </button>
    {/if}
    <details>
      <summary>Audit trail</summary>
      <h3>Plan</h3>
      <p>{result.audit.reasoning}</p>
      <p>
        Sources: {result.audit.data_sources.join(', ') || 'None'} · Attempts: {result.audit
          .attempts}
      </p>
      {#if result.audit.entities.length}
        <h3>Resolved entities</h3>
        <ul>
          {#each result.audit.entities as entity, index (index)}
            <li>
              {entity.mention} → {entity.resolved_to} ({entity.domain}, {entity.score.toFixed(1)}%, {entity.source})
            </li>
          {/each}
        </ul>
      {/if}
      {#if result.audit.checks.length}
        <h3>Guardrail</h3>
        <ul>
          {#each result.audit.checks as check (check.name)}
            <li>{check.passed ? 'Pass' : 'Fail'} · {check.name}: {check.detail}</li>
          {/each}
        </ul>
      {/if}
      {#if result.audit.sql}<h3>SQL</h3>
        <pre>{result.audit.sql}</pre>{/if}
    </details>
  </div>
</article>

<style>
  .question {
    align-self: flex-end;
    max-width: 713px;
    padding: 17px 21px;
    border-radius: 17px 4px 17px 17px;
    background: var(--brand);
    color: #fff;
    line-height: 25px;
    overflow-wrap: anywhere;
  }
  article {
    box-shadow: 0 8px 34px #143e4512;
  }
  header {
    padding: 9px 30px;
    border-bottom: 1px solid #e6eded;
    color: var(--muted);
    font-size: 12.7px;
  }
  .content {
    padding: 30px;
  }
  h2 {
    font-size: 21px;
  }
  .summary {
    margin-top: 8px;
    color: #5e7479;
    line-height: 25px;
    white-space: pre-wrap;
  }
  dl {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 13px;
    margin: 25px 0;
  }
  dl div {
    padding: 17px;
    border-radius: 13px;
    background: #f1f8f8;
  }
  dt,
  th {
    color: var(--muted);
    font-size: 12.7px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
  }
  dd {
    margin: 8px 0 0;
    font-size: 25px;
  }
  .scroll {
    max-height: 480px;
    overflow: auto;
    border: 1px solid #dfe8e9;
    border-radius: 13px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th,
  td {
    padding: 13px 17px;
    text-align: left;
    font-weight: 400;
  }
  thead {
    background: #f5f8f8;
  }
  td {
    border-top: 1px solid #e7eeee;
    font-size: 14.8px;
  }
  .download {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 25px 0 0;
    color: var(--action);
  }
  details {
    margin-top: 25px;
  }
  summary {
    cursor: pointer;
    color: var(--brand);
  }
  details h3 {
    margin: 16px 0 6px;
  }
  pre {
    padding: 16px;
    border-radius: 12px;
    background: #f5f8f8;
    overflow-x: auto;
  }
  .note {
    margin-top: 8px;
  }
</style>
