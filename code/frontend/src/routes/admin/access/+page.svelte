<script lang="ts">
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import { resources, users } from '#lib/demo.ts';
  let search = $state('');
  let selectedId = $state(users[0].id);
  const visible = $derived(
    users.filter((user) =>
      `${user.name} ${user.email}`.toLowerCase().includes(search.toLowerCase()),
    ),
  );
</script>

<DemoNotice />
<section class="card panel">
  <h1>Users &amp; Resources access</h1>
  <div class="people">
    <input type="search" aria-label="Search users" placeholder="Search users" bind:value={search} />
    {#each visible as user (user.id)}
      <button
        class="person"
        aria-label={`${user.name} ${user.email}`}
        aria-pressed={user.id === selectedId}
        onclick={() => (selectedId = user.id)}
      >
        <img src="/images/avatar.svg" alt="" />{user.name}
      </button>
    {/each}
    <button class="btn primary add" disabled>Add User +</button>
  </div>
  <div class="files">
    {#each resources as resource (resource.name)}
      <label>
        <input type="checkbox" checked={resource.granted} disabled /><span>
          {resource.name}<small>{resource.meta}</small>
        </span>
      </label>
    {/each}
    <footer>
      <button class="link danger-text" disabled>Remove user</button>
      <button class="btn" disabled>Cancel</button>
      <button class="btn primary" disabled>Save access</button>
    </footer>
  </div>
</section>

<style>
  .panel {
    display: grid;
    grid-template-columns: 327px 1fr;
    min-height: 700px;
    border-radius: 23px;
    overflow: hidden;
    font-family: var(--sans);
  }
  h1 {
    grid-column: 1 / -1;
    height: 76px;
    padding: 22px;
    border-bottom: 1px solid #e5eded;
    font-size: 26px;
  }
  .people {
    display: flex;
    flex-direction: column;
    border-right: 3px solid #ededed;
  }
  .people input {
    height: 50px;
    margin: 9px 7px 4px;
    padding: 0 14px;
    border: 1px solid #cacaca;
    border-radius: 8px;
  }
  .person {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 17px;
  }
  .person[aria-pressed='true'] {
    background: #0b71814d;
  }
  .add {
    margin: auto 10px 10px;
  }
  .files {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
  }
  .files label {
    display: flex;
    align-items: center;
    gap: 16px;
    height: 74px;
    padding: 16px;
    border: 1px solid #e1e9ea;
    border-radius: 12px;
  }
  small {
    display: block;
    margin-top: 4px;
    color: var(--muted);
  }
  footer {
    display: flex;
    gap: 8px;
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid #e5eded;
  }
  footer .link {
    margin-right: auto;
  }
</style>
