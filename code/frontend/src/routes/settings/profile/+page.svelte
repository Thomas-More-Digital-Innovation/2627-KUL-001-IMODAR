<script lang="ts">
  import { page } from '$app/state';
  import Button from '#lib/components/Button.svelte';
  import Card from '#lib/components/Card.svelte';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  import Field from '#lib/components/Field.svelte';
  const user = $derived(page.data.user);
</script>

<DemoNotice>Profile editing is not connected yet.</DemoNotice>
<Card class="mt-4 rounded-2xl shadow-[0_1px_3px_#0000001a]">
  <header class="border-b border-[#e5eded] p-6">
    <h1 class="text-[18px]">Profile information</h1>
    <p class="mt-1.5 text-muted">Update how you appear across the workspace.</p>
  </header>
  <form class="grid grid-cols-2 gap-5 p-6" onsubmit={(event) => event.preventDefault()}>
    <div class="col-span-full flex gap-4">
      <img class="rounded-full" src="/images/avatar-lg.svg" alt="" />
      <div>
        <Button type="button" disabled>Change photo</Button>
        <p class="mt-1.5 text-muted">JPG or PNG, up to 2 MB.</p>
      </div>
    </div>
    <Field label="Full name"><input value={user?.full_name} autocomplete="name" readonly /></Field>
    <Field label="Role"><input value={user?.role} readonly /></Field>
    <Field label="Email address" class="col-span-full">
      <input type="email" value={user?.email} autocomplete="email" readonly />
    </Field>
    <Button variant="primary" class="col-start-2 justify-self-end" disabled>Save changes</Button>
  </form>
</Card>
