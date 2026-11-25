<script lang="ts">
  import Button from '#lib/components/Button.svelte';
  import Card from '#lib/components/Card.svelte';
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
<Card
  class="grid min-h-[700px] grid-cols-[327px_1fr] overflow-hidden rounded-[23px] font-sans shadow-[0_1px_3px_#0000001a]"
>
  <h1 class="col-span-full h-[76px] border-b border-[#e5eded] p-[22px] text-[26px]">
    Users &amp; Resources access
  </h1>
  <div class="flex flex-col border-r-3 border-[#ededed]">
    <input
      class="mx-[7px] mt-[9px] mb-1 h-[50px] rounded-lg border border-[#cacaca] bg-white px-3.5"
      type="search"
      aria-label="Search users"
      placeholder="Search users"
      bind:value={search}
    />
    {#each visible as user (user.id)}
      <button
        class="flex items-center gap-3 px-[17px] py-2.5 aria-pressed:bg-brand/30"
        aria-label={`${user.name} ${user.email}`}
        aria-pressed={user.id === selectedId}
        onclick={() => (selectedId = user.id)}
      >
        <img src="/images/avatar.svg" alt="" />{user.name}
      </button>
    {/each}
    <Button variant="primary" class="mx-2.5 mt-auto mb-2.5" disabled>Add User +</Button>
  </div>
  <div class="flex flex-col gap-2 p-4">
    {#each resources as resource (resource.name)}
      <label class="flex h-[74px] items-center gap-4 rounded-xl border border-[#e1e9ea] p-4">
        <input type="checkbox" checked={resource.granted} disabled /><span>
          {resource.name}<small class="mt-1 block text-[12px] text-muted">{resource.meta}</small>
        </span>
      </label>
    {/each}
    <footer class="mt-auto flex gap-2 border-t border-[#e5eded] pt-4">
      <Button variant="danger-link" class="mr-auto" disabled>Remove user</Button>
      <Button disabled>Cancel</Button>
      <Button variant="primary" disabled>Save access</Button>
    </footer>
  </div>
</Card>
