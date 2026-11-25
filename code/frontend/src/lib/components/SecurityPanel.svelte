<script lang="ts">
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';

  import Button from './Button.svelte';
  import Card from './Card.svelte';
  import Field from './Field.svelte';
  import Notice from './Notice.svelte';

  let current = $state('');
  let next = $state('');
  let confirmation = $state('');
  let busy = $state(false);
  let message = $state('');
  let error = $state('');

  async function run(action: () => Promise<void>, success: string) {
    busy = true;
    message = '';
    error = '';
    try {
      await action();
      message = success;
    } catch (cause) {
      error = messageOf(cause);
    } finally {
      busy = false;
    }
  }

  function changePassword(event: SubmitEvent) {
    event.preventDefault();
    if (next !== confirmation) {
      message = '';
      error = 'The new passwords do not match.';
      return;
    }
    void run(async () => {
      await auth.changePassword({ current_password: current, new_password: next });
      current = next = confirmation = '';
    }, 'Password updated. Other devices were signed out.');
  }
</script>

<div class="grid gap-6 font-sans">
  {#if message}<Notice role="status">{message}</Notice>{/if}
  {#if error}<Notice role="alert">{error}</Notice>{/if}
  <Card class="rounded-2xl shadow-[0_1px_3px_#0000001a]">
    <h2 class="px-6 py-[22px] text-[18px]">Password &amp; authentication</h2>
    <form class="grid grid-cols-2 gap-5 border-t border-[#e5eded] p-6" onsubmit={changePassword}>
      <Field label="Current password" class="col-span-full">
        <input
          type="password"
          autocomplete="current-password"
          maxlength="128"
          placeholder="Enter current password"
          required
          bind:value={current}
        />
      </Field>
      <Field label="New password">
        <input
          type="password"
          autocomplete="new-password"
          minlength="12"
          maxlength="128"
          placeholder="At least 12 characters"
          required
          bind:value={next}
        />
      </Field>
      <Field label="Confirm password">
        <input
          type="password"
          autocomplete="new-password"
          placeholder="Repeat new password"
          required
          bind:value={confirmation}
        />
      </Field>
      <Button variant="primary" class="col-start-2 justify-self-end" disabled={busy}>
        Update password
      </Button>
    </form>
  </Card>
  <Card
    class="flex items-center justify-between rounded-2xl py-3 pr-6 shadow-[0_1px_3px_#0000001a]"
  >
    <h2 class="px-6 py-[22px] text-[18px]">Two-factor authentication</h2>
    <span class="mt-1 text-muted">On · required for every account</span>
  </Card>
  <Card class="rounded-2xl p-6 shadow-[0_1px_3px_#0000001a]">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-[18px]">Active sessions</h2>
        <p class="mt-1 text-muted">Devices currently signed in to your account.</p>
      </div>
      <Button
        variant="danger-outline"
        disabled={busy}
        onclick={() => run(auth.revokeOthers, 'Other devices were signed out.')}
      >
        Sign out others
      </Button>
    </div>
    <div class="mt-5 rounded-xl bg-[#f4f8f8] p-4">
      This device
      <p class="mt-1 text-muted">Current session</p>
    </div>
  </Card>
</div>
