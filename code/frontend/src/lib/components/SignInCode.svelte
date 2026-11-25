<script lang="ts">
  import Field from './Field.svelte';
  let { label, code = $bindable('') }: { label: string; code: string } = $props();
</script>

<Field {label}>
  <input
    autocomplete="one-time-code"
    autocapitalize="off"
    spellcheck="false"
    minlength="6"
    maxlength="32"
    required
    bind:value={code}
  />
</Field>
