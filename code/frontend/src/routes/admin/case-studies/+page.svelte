<script lang="ts">
  import Badge from '#lib/components/Badge.svelte';
  import BulkBar from '#lib/components/BulkBar.svelte';
  import Button from '#lib/components/Button.svelte';
  import DataTable from '#lib/components/DataTable.svelte';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import Dialog from '#lib/components/Dialog.svelte';
  import Field from '#lib/components/Field.svelte';
  import FilterBar from '#lib/components/FilterBar.svelte';
  import PageHead from '#lib/components/PageHead.svelte';
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

<PageHead title="Case studies">
  <Button
    onclick={() =>
      downloadCsv(
        'case-studies.csv',
        ['Title', 'Level', 'Status'],
        visible.map((paper) => [paper.title, paper.level, paper.status]),
      )}
  >
    Export CSV
  </Button>
  <Button variant="primary" onclick={() => (importOpen = true)}>Import paper</Button>
</PageHead>
<DemoNotice />
<FilterBar>
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
</FilterBar>
<BulkBar count={selected.length} onclear={() => (selected = [])}>
  <Button variant="link" disabled>Change level</Button>
  <Button variant="link" disabled>Archive</Button>
  <Button variant="danger-link" onclick={() => confirmDelete([...selected])}>Delete</Button>
</BulkBar>
<DataTable
  columns={['Paper', 'Access level', 'Status', 'Updated', 'Actions']}
  summary={`Showing ${visible.length} of ${papers.length} papers`}
>
  {#each visible as paper (paper.id)}
    <tr>
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
        <Button variant="link" disabled>View</Button>
        <Button variant="link" disabled>Edit</Button>
        <Button
          variant="danger-link"
          aria-label={`Delete ${paper.title}`}
          onclick={() => confirmDelete([paper.id])}
        >
          Delete
        </Button>
      </td>
    </tr>
  {/each}
</DataTable>

<Dialog title={`${deleteLabel}?`} bind:open={deleteOpen}>
  <p>
    This permanently deletes the selected papers and their files. Members will lose access. This
    action cannot be undone.
  </p>
  <ul class="list-disc pl-10">
    {#each targets as paper (paper.id)}
      <li>{paper.title} <small class="text-[12px]">Level {paper.level} · {paper.status}</small></li>
    {/each}
  </ul>
  {#snippet actions()}<Button variant="danger" disabled>{deleteLabel}</Button>{/snippet}
</Dialog>
<Dialog title="Import paper" bind:open={importOpen}>
  <Field label="Paper file"><input type="file" accept="application/pdf" /></Field>
  <Field label="Paper title"><input /></Field>
  <Field label="Authors"><input /></Field>
  <Field label="DOI (optional)"><input placeholder="Add a DOI" /></Field>
  <Field label="Access level">
    <select value={3}>
      {#each levels as option (option)}<option value={option}>Level {option}</option>{/each}
    </select>
  </Field>
  {#snippet actions()}<Button variant="primary" disabled>Import file</Button>{/snippet}
</Dialog>
