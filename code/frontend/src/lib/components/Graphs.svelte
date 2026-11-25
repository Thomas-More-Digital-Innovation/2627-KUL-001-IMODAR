<script lang="ts">
  import type { GraphReport } from '#lib/api/client.ts';
  import Notice from './Notice.svelte';
  let { report, truncatedTo }: { report: GraphReport; truncatedTo: number | null } = $props();
</script>

<section data-testid="graphs" class="mt-[25px] grid gap-4">
  <h3 class="text-[17px]">Graphs</h3>
  {#if report.error}
    <Notice role="alert">{report.error}</Notice>
  {:else if !report.items.length}
    <p>No meaningful graph was found for this result.</p>
  {/if}
  {#if truncatedTo !== null && report.items.length}
    <Notice role="note">Graphs use only the first {truncatedTo} rows.</Notice>
  {/if}
  {#each report.items as graph, index (index)}
    {@const source = `data:image/png;base64,${graph.png_base64}`}
    <figure class="rounded-[13px] border border-line p-4">
      <img class="mx-auto" src={source} alt={`${graph.title}. ${graph.rationale}`} />
      <figcaption class="mt-3 flex items-center justify-between gap-4 text-muted">
        <span>{graph.rationale}</span>
        <a class="shrink-0 text-action" href={source} download={`graph-${index + 1}.png`}>
          Download PNG
        </a>
      </figcaption>
    </figure>
  {/each}
  {#if report.rejected.length}
    <details>
      <summary class="cursor-pointer text-brand">Rejected suggestions</summary>
      <ul class="my-3.5 list-disc pl-10">
        {#each report.rejected as item, index (index)}
          <li>{item.title} ({item.type}): {item.reason}</li>
        {/each}
      </ul>
    </details>
  {/if}
</section>
