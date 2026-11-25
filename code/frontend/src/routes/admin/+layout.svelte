<script lang="ts">
  import { page } from '$app/state';
  import type { LayoutProps } from './$types';
  let { children }: LayoutProps = $props();
  const links = [
    { href: '/admin/users', label: 'Users', icon: 'user' },
    { href: '/admin/security', label: 'Security', icon: 'shield' },
    { href: '/admin/case-studies', label: 'Case studies', icon: 'case-study' },
    { href: '/admin/access', label: 'Resource access', icon: 'users' },
  ];
</script>

<div class="shell">
  <header><a href="/">← Back to workspace</a><span class="logo">IMODAR</span></header>
  <nav aria-label="Workspace settings">
    <p>WORKSPACE SETTINGS</p>
    {#each links as link (link.href)}
      <a href={link.href} aria-current={page.url.pathname === link.href ? 'page' : undefined}>
        <span class="icon" style:mask-image={`url(/images/${link.icon}.svg)`}></span>{link.label}
      </a>
    {/each}
  </nav>
  <main>{@render children()}</main>
</div>

<style>
  .shell {
    display: grid;
    grid-template-columns: 232px minmax(0, 1fr);
    grid-template-rows: 76px 1fr;
    min-height: 100vh;
    background: var(--admin-bg);
    font-family: var(--admin);
  }
  header {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px 0 32px;
    background: #fff;
    color: var(--brand);
    font-size: 16px;
  }
  nav {
    padding: 34px 16px;
    background: #fff;
    font-size: 17px;
  }
  nav p {
    margin: 0 8px 30px;
    color: #637d85;
    font-size: 11px;
    font-weight: 700;
  }
  nav a {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 48px;
    margin-bottom: 12px;
    padding: 0 10px;
    border-radius: 8px;
    color: #576f77;
  }
  nav a[aria-current] {
    background: var(--tint);
    color: var(--brand);
    font-weight: 700;
  }
  .icon {
    width: 30px;
    height: 30px;
    background: currentColor;
    mask-position: center;
    mask-repeat: no-repeat;
    mask-size: contain;
  }
  main {
    display: grid;
    align-content: start;
    gap: 16px;
    padding: 40px 48px;
    min-width: 0;
  }
  main :global(.head),
  main :global(.filters),
  main :global(.bulk) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
  }
  main :global(.head h1) {
    flex: 1;
    color: #183b44;
    font-size: 34px;
    font-weight: 700;
  }
  main :global(.primary) {
    background: var(--brand);
  }
  main :global(.filters > *),
  main :global(td select) {
    min-height: 44px;
    padding: 0 14px;
    border: 1px solid #d3e0e4;
    border-radius: 8px;
    background: #fff;
  }
  main :global(.filters input) {
    flex: 1;
    min-width: 200px;
  }
  main :global(.bulk) {
    min-height: 46px;
    padding: 0 16px;
    border-radius: 8px;
    background: var(--tint);
  }
  main :global(.table) {
    border-radius: 12px;
    overflow-x: auto;
  }
  main :global(table) {
    width: 100%;
    border-collapse: collapse;
  }
  main :global(th) {
    padding: 16px 12px;
    background: #f8fafb;
    color: #637d85;
    font-size: 13px;
    text-align: left;
  }
  main :global(td) {
    padding: 10px 12px;
    border-bottom: 1px solid #e6edef;
  }
  main :global(tr.selected) {
    background: #f4fafb;
  }
  main :global(td small) {
    display: block;
    margin-top: 4px;
    color: #637d85;
  }
  main :global(.foot) {
    padding: 16px 24px;
    color: #637d85;
    font-size: 13px;
  }
</style>
