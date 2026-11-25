<script lang="ts">
  import { page } from '$app/state';
  import DemoNotice from '#lib/components/DemoNotice.svelte';
  const user = $derived(page.data.user);
</script>

<DemoNotice>Profile editing is not connected yet.</DemoNotice>
<section class="card">
  <header>
    <h1>Profile information</h1>
    <p>Update how you appear across the workspace.</p>
  </header>
  <form onsubmit={(event) => event.preventDefault()}>
    <div class="photo wide">
      <img src="/images/avatar-lg.svg" alt="" />
      <div>
        <button type="button" class="btn" disabled>Change photo</button>
        <p>JPG or PNG, up to 2 MB.</p>
      </div>
    </div>
    <label class="field">
      Full name<input value={user?.full_name} autocomplete="name" readonly />
    </label>
    <label class="field">Role<input value={user?.role} readonly /></label>
    <label class="field wide">
      Email address<input type="email" value={user?.email} autocomplete="email" readonly />
    </label>
    <button class="btn primary" disabled>Save changes</button>
  </form>
</section>

<style>
  section {
    margin-top: 16px;
  }
  header {
    padding: 24px;
    border-bottom: 1px solid #e5eded;
  }
  h1 {
    font-size: 18px;
  }
  p {
    margin-top: 6px;
    color: var(--muted);
  }
  form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 24px;
  }
  .wide {
    grid-column: 1 / -1;
  }
  .photo img {
    border-radius: 50%;
  }
  .photo {
    display: flex;
    gap: 16px;
  }
  .primary {
    grid-column: 2;
    justify-self: end;
    border-radius: 12px;
  }
</style>
