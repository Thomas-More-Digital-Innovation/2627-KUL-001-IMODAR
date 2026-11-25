<script lang="ts">
  import Logo from '#lib/components/Logo.svelte';
  import MaskIcon from '#lib/components/MaskIcon.svelte';
  import { page } from '$app/state';
  import type { LayoutProps } from './$types';
  let { children }: LayoutProps = $props();
  const links = [
    { href: '/settings/profile', label: 'Profile', icon: 'user' },
    { href: '/settings/security', label: 'Security', icon: 'shield' },
  ];
</script>

<header
  class="flex min-h-[59px] items-center justify-between border border-[#adadad] bg-white pr-[17px] pl-[29px] text-[23.7px] text-brand shadow-[0_4px_25px_#0000001a]"
>
  <a href="/">← Back to workspace</a><Logo />
</header>
<div class="grid grid-cols-[minmax(200px,343px)_minmax(0,950px)] gap-[29px] px-[54px] py-[68px]">
  <nav
    class="grid gap-2 self-start rounded-2xl border border-[#adadad] bg-[#fffbfb] p-[11px] text-[26.5px]"
    aria-label="Settings"
  >
    {#each links as link (link.href)}
      <a
        class="flex h-[54px] items-center gap-3.5 rounded-lg px-2.5 text-[#4e4e4e] aria-[current]:bg-brand/30 aria-[current]:text-brand"
        href={link.href}
        aria-current={page.url.pathname === link.href ? 'page' : undefined}
      >
        <MaskIcon name={link.icon} class="size-[35px]" />{link.label}
      </a>
    {/each}
  </nav>
  <main>{@render children()}</main>
</div>
