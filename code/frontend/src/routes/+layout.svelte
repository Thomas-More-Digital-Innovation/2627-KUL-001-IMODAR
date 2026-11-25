<script lang="ts">
  import '@fontsource/line-seed-jp/latin-400.css';
  import '@fontsource/line-seed-jp/latin-800.css';
  import '@fontsource-variable/manrope';
  import '../app.css';
  import type { LayoutProps } from './$types';
  let { children }: LayoutProps = $props();
</script>

{@render children()}
