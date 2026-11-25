<script lang="ts">
  import Badge from '#lib/components/Badge.svelte';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import Dialog from '#lib/components/Dialog.svelte';
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

<div class="head">
  <h1>Users</h1>
  <button
    class="btn"
    onclick={() =>
      downloadCsv(
        'users.csv',
        ['Name', 'Email', 'Role', 'Status'],
        visible.map((user) => [user.name, user.email, user.role, user.status]),
      )}
  >
    Export CSV
  </button>
  <button class="btn primary" onclick={() => (inviteOpen = true)}>Invite user</button>
</div>
<DemoNotice />
<div class="filters">
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
</div>
{#if selected.length}
  <div class="bulk">
    <strong>{selected.length} selected</strong>
    <button class="link" disabled>Change role</button>
    <button class="link danger-text" disabled>Deactivate</button>
    <button onclick={() => (selected = [])}>Clear selection</button>
  </div>
{/if}
<div class="card table">
  <table>
    <thead>
      <tr>
        <th><span class="visually-hidden">Select</span></th><th>User</th><th>Role</th><th>
          Status
        </th><th>Last active</th><th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each visible as user (user.id)}
        <tr class:selected={selected.includes(user.id)}>
          <td>
            <input
              type="checkbox"
              aria-label={`Select ${user.email}`}
              value={user.id}
              bind:group={selected}
            />
          </td>
          <td>
            <div class="person">
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
            <button
              class="btn"
              onclick={() => {
                editing = user;
                editOpen = true;
              }}
            >
              Edit
            </button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
  <p class="foot">Showing {visible.length} of {users.length} users</p>
</div>
<section class="card levels">
  <h2>Role access levels</h2>
  {#each roles as option (option)}
    <label class="field">
      {option}<select value={defaultLevels[option]} disabled>
        {#each levels as level (level)}<option value={level}>Level {level}</option>{/each}
      </select>
    </label>
  {/each}
  <p>
    Users can access published papers at or below their role’s level. Levels 1–6 are available for
    every role.
  </p>
</section>

<Dialog title="Invite user" bind:open={inviteOpen}>
  <label class="field">
    Email address<input type="email" placeholder="colleague@example.com" />
  </label>
  <label class="field">
    Role<select value="Researcher">
      {#each roles as option (option)}<option>{option}</option>{/each}
    </select>
  </label>
  {#snippet actions()}<button class="btn primary" disabled>Send invitation</button>{/snippet}
</Dialog>
<Dialog title="Edit user" bind:open={editOpen}>
  <label class="field">Full name<input value={editing.name} /></label>
  <label class="field">Email address<input type="email" value={editing.email} /></label>
  <label class="field">
    Role<small>Choose the lowest level of access this person needs.</small><select
      value={editing.role}
    >
      {#each roles as option (option)}<option>{option}</option>{/each}
    </select>
  </label>
  <div>Workspace access <Badge status={editing.status} /></div>
  <button class="btn" disabled>Deactivate user</button>
  {#snippet actions()}<button class="btn primary" disabled>Save changes</button>{/snippet}
</Dialog>

<style>
  .person {
    display: flex;
    align-items: center;
    gap: 18px;
    font-size: 16px;
    font-weight: 600;
  }
  .person small {
    font-size: 12px;
    font-weight: 400;
  }
  .levels {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 16px;
    padding: 20px 24px;
  }
  h2 {
    font-size: 16px;
    font-weight: 700;
  }
  .levels p {
    grid-column: 1 / -1;
    font-size: 12px;
  }
</style>
