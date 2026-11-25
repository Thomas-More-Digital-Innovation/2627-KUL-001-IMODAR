<script lang="ts">
  import { page } from '$app/state';
  import type { LayoutProps } from './$types';
  let { children }: LayoutProps = $props();
  const links = [
    { href: '/settings/profile', label: 'Profile', icon: 'user' },
    { href: '/settings/security', label: 'Security', icon: 'shield' },
  ];
</script>

<header><a href="/">← Back to workspace</a><span class="logo">IMODAR</span></header>
<div class="layout">
  <nav aria-label="Settings">
    {#each links as link (link.href)}
      <a href={link.href} aria-current={page.url.pathname === link.href ? 'page' : undefined}>
        <span class="icon" style:mask-image={`url(/images/${link.icon}.svg)`}></span>{link.label}
      </a>
    {/each}
  </nav>
  <main>{@render children()}</main>
</div>

<style>
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 59px;
    padding: 0 17px 0 29px;
    border: 1px solid #adadad;
    background: #fff;
    color: var(--brand);
    font-size: 23.7px;
    box-shadow: 0 4px 25px #0000001a;
  }
  .layout {
    display: grid;
    grid-template-columns: minmax(200px, 343px) minmax(0, 950px);
    gap: 29px;
    padding: 68px 54px;
  }
  nav {
    align-self: start;
    display: grid;
    gap: 8px;
    padding: 11px;
    border: 1px solid #adadad;
    border-radius: 16px;
    background: #fffbfb;
    font-size: 26.5px;
  }
  nav a {
    display: flex;
    align-items: center;
    gap: 14px;
    height: 54px;
    padding: 0 10px;
    border-radius: 8px;
    color: #4e4e4e;
  }
  nav a[aria-current] {
    background: #0b71814d;
    color: var(--brand);
  }
  .icon {
    width: 35px;
    height: 35px;
    background: currentColor;
  }
</style>
