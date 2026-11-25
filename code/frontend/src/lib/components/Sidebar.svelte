<script lang="ts">
  import { page } from '$app/state';
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';
  import { analyses } from '#lib/analyses.svelte.ts';
  let menuOpen = $state(false);
  let error = $state('');
  const user = $derived(page.data.user);

  async function logout() {
    try {
      await auth.logout();
      // A full load clears analyses held in memory.
      window.location.assign('/login');
    } catch (cause) {
      error = messageOf(cause);
    }
  }
</script>

<aside>
  <a class="logo" href="/">IMODAR</a>
  <button class="new" disabled={!!analyses.pending} onclick={() => analyses.select(null)}>
    + New analysis
  </button>
  <h2>Recent analysis</h2>
  <nav aria-label="Recent analysis">
    {#each analyses.items as item (item.id)}
      <button
        class:active={item.id === analyses.activeId}
        aria-current={item.id === analyses.activeId || undefined}
        disabled={!!analyses.pending}
        onclick={() => analyses.select(item.id)}
      >
        {item.title}
      </button>
    {/each}
  </nav>
  {#if menuOpen}
    <div class="menu" id="user-menu">
      <a href="/settings/profile">Settings</a>
      {#if user?.role === 'admin'}<a href="/admin/users">Dashboard</a>{/if}
      <button onclick={logout}>Log out</button>
      {#if error}<p role="alert">{error}</p>{/if}
    </div>
  {/if}
  <button
    class="user"
    aria-expanded={menuOpen}
    aria-controls="user-menu"
    onclick={() => (menuOpen = !menuOpen)}
  >
    <img src="/images/avatar.svg" alt="" width="41" height="41" />
    <span>{user?.full_name}<br />{user?.email}</span><b aria-hidden="true">
      {menuOpen ? '↓' : '↑'}
    </b>
  </button>
</aside>

<style>
  aside {
    display: flex;
    flex-direction: column;
    width: clamp(230px, 27vw, 388px);
    flex-shrink: 0;
    height: 100vh;
    padding: 18px 16px 13px;
    background: var(--navy);
    color: #fff;
  }
  .logo {
    padding-left: 8px;
  }
  .new {
    min-height: 55px;
    margin: 58px 0 36px;
    padding: 0 9px;
    border-radius: 8px;
    background: #fff;
    color: var(--navy);
    font-size: 23.7px;
    text-align: left;
  }
  h2 {
    font-size: 26.5px;
    margin-bottom: 10px;
  }
  nav {
    flex: 1;
    overflow-y: auto;
  }
  nav button {
    width: 100%;
    min-height: 63px;
    padding: 12px 17px;
    border-radius: 17px;
    overflow: hidden;
    color: #ecfeffcc;
    font-size: 20px;
    text-align: left;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  nav .active {
    background: #ffffff1f;
    color: #fff;
  }
  .menu,
  .user {
    border: 1px dashed #4ba1b1;
    border-radius: 17px;
    background: #ffffff1f;
    font-size: 18px;
  }
  .menu {
    display: grid;
    margin-bottom: 5px;
    padding: 5px;
  }
  .menu a,
  .menu button {
    text-align: left;
    padding: 5px 13px;
    border-radius: 17px;
  }
  .menu a:hover,
  .menu button:hover {
    background: #ffffff1f;
  }
  .user {
    display: flex;
    align-items: center;
    gap: 14px;
    min-height: 63px;
    padding: 5px 10px;
    text-align: left;
  }
  .user span {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
