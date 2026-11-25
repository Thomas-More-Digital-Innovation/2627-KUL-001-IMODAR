<script lang="ts">
  import { page } from '$app/state';
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';
  import { analyses } from '#lib/analyses.svelte.ts';
  import Logo from './Logo.svelte';
  const menuItem = 'rounded-[17px] px-[13px] py-[5px] text-left hover:bg-white/12';
  const panel = 'rounded-[17px] border border-dashed border-[#4ba1b1] bg-white/12 text-[18px]';
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

<aside
  class="flex h-screen w-[clamp(230px,27vw,388px)] shrink-0 flex-col bg-navy px-4 pt-[18px] pb-[13px] text-white"
>
  <a class="pl-2" href="/"><Logo /></a>
  <button
    class="mt-[58px] mb-9 min-h-[55px] rounded-lg bg-white px-[9px] text-left text-[23.7px] text-navy"
    disabled={!!analyses.pending}
    onclick={() => analyses.select(null)}
  >
    + New analysis
  </button>
  <h2 class="mb-2.5 text-[26.5px]">Recent analysis</h2>
  <nav class="flex-1 overflow-y-auto" aria-label="Recent analysis">
    {#each analyses.items as item (item.id)}
      <button
        class={[
          'min-h-[63px] w-full truncate rounded-[17px] px-[17px] py-3 text-left text-[20px]',
          item.id === analyses.activeId ? 'bg-white/12 text-white' : 'text-[#ecfeffcc]',
        ]}
        aria-current={item.id === analyses.activeId || undefined}
        disabled={!!analyses.pending}
        onclick={() => analyses.select(item.id)}
      >
        {item.title}
      </button>
    {/each}
  </nav>
  {#if menuOpen}
    <div class={[panel, 'mb-[5px] grid p-[5px]']} id="user-menu">
      <a class={menuItem} href="/settings/profile">Settings</a>
      {#if user?.role === 'admin'}<a class={menuItem} href="/admin/users">Dashboard</a>{/if}
      <button class={menuItem} onclick={logout}>Log out</button>
      {#if error}<p role="alert">{error}</p>{/if}
    </div>
  {/if}
  <button
    class={[panel, 'flex min-h-[63px] items-center gap-3.5 px-2.5 py-[5px] text-left']}
    aria-expanded={menuOpen}
    aria-controls="user-menu"
    onclick={() => (menuOpen = !menuOpen)}
  >
    <img src="/images/avatar.svg" alt="" width="41" height="41" />
    <span class="min-w-0 flex-1 overflow-hidden text-ellipsis">
      {user?.full_name}<br />{user?.email}
    </span><b aria-hidden="true">
      {menuOpen ? '↓' : '↑'}
    </b>
  </button>
</aside>
