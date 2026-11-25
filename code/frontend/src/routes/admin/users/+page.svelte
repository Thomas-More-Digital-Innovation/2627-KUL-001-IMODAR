<script lang="ts">
  import Badge from '#lib/components/Badge.svelte';
  import BulkBar from '#lib/components/BulkBar.svelte';
  import Button from '#lib/components/Button.svelte';
  import Card from '#lib/components/Card.svelte';
  import DataTable from '#lib/components/DataTable.svelte';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import Dialog from '#lib/components/Dialog.svelte';
  import Field from '#lib/components/Field.svelte';
  import FilterBar from '#lib/components/FilterBar.svelte';
  import PageHead from '#lib/components/PageHead.svelte';
  import { downloadCsv } from '#lib/csv.ts';
  import { levels, roles, users } from '#lib/demo.ts';

  let search = $state('');
  let role = $state('');
  let status = $state('');
  let selected = $state<number[]>([]);
  let inviteOpen = $state(false);
  let editOpen = $state(false);
  let editing = $state(users[0]);
  const statuses = [...new Set(users.map((user) => user.status))];
  const defaultLevels: Record<string, number> = { Intern: 1, Researcher: 3, Admin: 6 };
  const visible = $derived(
    users.filter(
      (user) =>
        `${user.name} ${user.email}`.toLowerCase().includes(search.toLowerCase()) &&
        (!role || user.role === role) &&
        (!status || user.status === status),
    ),
  );
</script>

<PageHead title="Users">
  <Button
    onclick={() =>
      downloadCsv(
        'users.csv',
        ['Name', 'Email', 'Role', 'Status'],
        visible.map((user) => [user.name, user.email, user.role, user.status]),
      )}
  >
    Export CSV
  </Button>
  <Button variant="primary" onclick={() => (inviteOpen = true)}>Invite user</Button>
</PageHead>
<DemoNotice />
<FilterBar>
  <input
    type="search"
    aria-label="Search users"
    placeholder="Search by name or email"
    bind:value={search}
  />
  <select aria-label="Filter by role" bind:value={role}>
    <option value="">All roles</option>
    {#each roles as option (option)}<option>{option}</option>{/each}
  </select>
  <select aria-label="Filter by status" bind:value={status}>
    <option value="">All statuses</option>
    {#each statuses as option (option)}<option>{option}</option>{/each}
  </select>
  <button
    onclick={() => {
      search = '';
      role = '';
      status = '';
    }}
  >
    Clear filters
  </button>
</FilterBar>
<BulkBar count={selected.length} onclear={() => (selected = [])}>
  <Button variant="link" disabled>Change role</Button>
  <Button variant="danger-link" disabled>Deactivate</Button>
</BulkBar>
<DataTable
  columns={['User', 'Role', 'Status', 'Last active', 'Actions']}
  summary={`Showing ${visible.length} of ${users.length} users`}
>
  {#each visible as user (user.id)}
    <tr>
      <td>
        <input
          type="checkbox"
          aria-label={`Select ${user.email}`}
          value={user.id}
          bind:group={selected}
        />
      </td>
      <td>
        <div class="flex items-center gap-[18px] text-[16px] font-semibold">
          <img src="/images/avatar.svg" alt="" />
          <div>{user.name}<small>{user.email}</small></div>
        </div>
      </td>
      <td>
        <select aria-label={`Role of ${user.email}`} value={user.role} disabled>
          {#each roles as option (option)}<option>{option}</option>{/each}
        </select>
      </td>
      <td><Badge status={user.status} /></td>
      <td>{user.seen}</td>
      <td>
        <Button
          onclick={() => {
            editing = user;
            editOpen = true;
          }}
        >
          Edit
        </Button>
      </td>
    </tr>
  {/each}
</DataTable>
<Card
  class="grid grid-cols-[2fr_1fr_1fr_1fr] gap-4 rounded-2xl px-6 py-5 shadow-[0_1px_3px_#0000001a]"
>
  <h2 class="text-[16px] font-bold">Role access levels</h2>
  {#each roles as option (option)}
    <Field label={option}>
      <select value={defaultLevels[option]} disabled>
        {#each levels as level (level)}<option value={level}>Level {level}</option>{/each}
      </select>
    </Field>
  {/each}
  <p class="col-span-full text-[12px]">
    Users can access published papers at or below their role’s level. Levels 1–6 are available for
    every role.
  </p>
</Card>

<Dialog title="Invite user" bind:open={inviteOpen}>
  <Field label="Email address"><input type="email" placeholder="colleague@example.com" /></Field>
  <Field label="Role">
    <select value="Researcher">
      {#each roles as option (option)}<option>{option}</option>{/each}
    </select>
  </Field>
  {#snippet actions()}<Button variant="primary" disabled>Send invitation</Button>{/snippet}
</Dialog>
<Dialog title="Edit user" bind:open={editOpen}>
  <Field label="Full name"><input value={editing.name} /></Field>
  <Field label="Email address"><input type="email" value={editing.email} /></Field>
  <Field label="Role" hint="Choose the lowest level of access this person needs.">
    <select value={editing.role}>
      {#each roles as option (option)}<option>{option}</option>{/each}
    </select>
  </Field>
  <div>Workspace access <Badge status={editing.status} /></div>
  <Button disabled>Deactivate user</Button>
  {#snippet actions()}<Button variant="primary" disabled>Save changes</Button>{/snippet}
</Dialog>
