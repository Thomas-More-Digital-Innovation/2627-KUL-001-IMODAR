<script lang="ts">
  let { label, code = $bindable('') }: { label: string; code: string } = $props();
</script>

<label class="field">
  {label}
  <input
    autocomplete="one-time-code"
    autocapitalize="off"
    spellcheck="false"
    minlength="6"
    maxlength="32"
    required
    bind:value={code}
  />
</label>
