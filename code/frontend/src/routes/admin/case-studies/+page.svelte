<script lang="ts">
  import Badge from '#lib/components/Badge.svelte';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import Dialog from '#lib/components/Dialog.svelte';
  import { downloadCsv } from '#lib/csv.ts';
  import { levels, papers } from '#lib/demo.ts';

  let search = $state('');
  let level = $state(0);
  let status = $state('');
  let selected = $state<number[]>([]);
  let importOpen = $state(false);
  let deleteOpen = $state(false);
  let deleting = $state<number[]>([]);
  const statuses = [...new Set(papers.map((paper) => paper.status))];
  const targets = $derived(papers.filter((paper) => deleting.includes(paper.id)));
  const deleteLabel = $derived(
    `Delete ${deleting.length} paper${deleting.length === 1 ? '' : 's'}`,
  );
  const visible = $derived(
    papers.filter(
      (paper) =>
        `${paper.title} ${paper.meta}`.toLowerCase().includes(search.toLowerCase()) &&
        (!level || paper.level === level) &&
        (!status || paper.status === status),
    ),
  );

  function confirmDelete(ids: number[]) {
    deleting = ids;
    deleteOpen = true;
  }
</script>

<div class="head">
  <h1>Case studies</h1>
  <button
    class="btn"
    onclick={() =>
      downloadCsv(
        'case-studies.csv',
        ['Title', 'Level', 'Status'],
        visible.map((paper) => [paper.title, paper.level, paper.status]),
      )}
  >
    Export CSV
  </button>
  <button class="btn primary" onclick={() => (importOpen = true)}>Import paper</button>
</div>
<DemoNotice />
<div class="filters">
  <input
    type="search"
    aria-label="Search papers"
    placeholder="Search by title, author or DOI"
    bind:value={search}
  />
  <select aria-label="Filter by level" bind:value={level}>
    <option value={0}>All levels</option>
    {#each levels as option (option)}<option value={option}>Level {option}</option>{/each}
  </select>
  <select aria-label="Filter by status" bind:value={status}>
    <option value="">All statuses</option>
    {#each statuses as option (option)}<option>{option}</option>{/each}
  </select>
</div>
{#if selected.length}
  <div class="bulk">
    <strong>{selected.length} selected</strong>
    <button class="link" disabled>Change level</button>
    <button class="link" disabled>Archive</button>
    <button class="link danger-text" onclick={() => confirmDelete([...selected])}>Delete</button>
    <button onclick={() => (selected = [])}>Clear selection</button>
  </div>
{/if}
<div class="card table">
  <table>
    <thead>
      <tr>
        <th><span class="visually-hidden">Select</span></th><th>Paper</th><th>Access level</th><th>
          Status
        </th><th>Updated</th><th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each visible as paper (paper.id)}
        <tr class:selected={selected.includes(paper.id)}>
          <td>
            <input
              type="checkbox"
              aria-label={`Select ${paper.title}`}
              value={paper.id}
              bind:group={selected}
            />
          </td>
          <td>{paper.title}<small>{paper.meta}</small></td>
          <td>
            <select aria-label={`Level of ${paper.title}`} value={paper.level} disabled>
              {#each levels as option (option)}<option value={option}>Level {option}</option>{/each}
            </select>
          </td>
          <td><Badge status={paper.status} /></td>
          <td>{paper.updated}</td>
          <td>
            <button class="link" disabled>View</button>
            <button class="link" disabled>Edit</button>
            <button
              class="link danger-text"
              aria-label={`Delete ${paper.title}`}
              onclick={() => confirmDelete([paper.id])}
            >
              Delete
            </button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
  <p class="foot">Showing {visible.length} of {papers.length} papers</p>
</div>

<Dialog title={`${deleteLabel}?`} bind:open={deleteOpen}>
  <p>
    This permanently deletes the selected papers and their files. Members will lose access. This
    action cannot be undone.
  </p>
  <ul>
    {#each targets as paper (paper.id)}
      <li>{paper.title} <small>Level {paper.level} · {paper.status}</small></li>
    {/each}
  </ul>
  {#snippet actions()}<button class="btn danger" disabled>{deleteLabel}</button>{/snippet}
</Dialog>
<Dialog title="Import paper" bind:open={importOpen}>
  <label class="field">Paper file<input type="file" accept="application/pdf" /></label>
  <label class="field">Paper title<input /></label>
  <label class="field">Authors<input /></label>
  <label class="field">DOI (optional)<input placeholder="Add a DOI" /></label>
  <label class="field">
    Access level<select value={3}>
      {#each levels as option (option)}<option value={option}>Level {option}</option>{/each}
    </select>
  </label>
  {#snippet actions()}<button class="btn primary" disabled>Import file</button>{/snippet}
</Dialog>
