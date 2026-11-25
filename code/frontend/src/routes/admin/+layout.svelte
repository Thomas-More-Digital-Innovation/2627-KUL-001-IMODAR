<script lang="ts">
  import Logo from '#lib/components/Logo.svelte';
  import MaskIcon from '#lib/components/MaskIcon.svelte';
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

<div
  class="grid min-h-screen grid-cols-[232px_minmax(0,1fr)] grid-rows-[76px_1fr] bg-admin-canvas font-admin"
>
  <header
    class="col-span-full flex items-center justify-between bg-white pr-7 pl-8 text-[16px] text-brand"
  >
    <a href="/">← Back to workspace</a><Logo />
  </header>
  <nav class="bg-white px-4 py-[34px] text-[17px]" aria-label="Workspace settings">
    <p class="mx-2 mb-[30px] text-[11px] font-bold text-[#637d85]">WORKSPACE SETTINGS</p>
    {#each links as link (link.href)}
      <a
        class="mb-3 flex h-12 items-center gap-3 rounded-lg px-2.5 text-[#576f77] aria-[current]:bg-tint aria-[current]:font-bold aria-[current]:text-brand"
        href={link.href}
        aria-current={page.url.pathname === link.href ? 'page' : undefined}
      >
        <MaskIcon name={link.icon} class="size-[30px]" />{link.label}
      </a>
    {/each}
  </nav>
  <!-- The admin designs use the brand colour for primary actions. -->
  <main class="grid min-w-0 content-start gap-4 px-12 py-10 [--color-action:var(--color-brand)]">
    {@render children()}
  </main>
</div>
