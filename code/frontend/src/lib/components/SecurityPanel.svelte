<script lang="ts">
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';

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

<div class="stack">
  {#if message}<p class="notice" role="status">{message}</p>{/if}
  {#if error}<p class="notice" role="alert">{error}</p>{/if}
  <section class="card">
    <h2>Password &amp; authentication</h2>
    <form onsubmit={changePassword}>
      <label class="field wide">
        Current password
        <input
          type="password"
          autocomplete="current-password"
          maxlength="128"
          placeholder="Enter current password"
          required
          bind:value={current}
        />
      </label>
      <label class="field">
        New password
        <input
          type="password"
          autocomplete="new-password"
          minlength="12"
          maxlength="128"
          placeholder="At least 12 characters"
          required
          bind:value={next}
        />
      </label>
      <label class="field">
        Confirm password
        <input
          type="password"
          autocomplete="new-password"
          placeholder="Repeat new password"
          required
          bind:value={confirmation}
        />
      </label>
      <button class="btn primary" disabled={busy}>Update password</button>
    </form>
  </section>
  <section class="card row">
    <h2>Two-factor authentication</h2>
    <span class="muted">On · required for every account</span>
  </section>
  <section class="card sessions">
    <div class="row">
      <div>
        <h2>Active sessions</h2>
        <p class="muted">Devices currently signed in to your account.</p>
      </div>
      <button
        class="btn out"
        disabled={busy}
        onclick={() => run(auth.revokeOthers, 'Other devices were signed out.')}
      >
        Sign out others
      </button>
    </div>
    <div class="session">
      This device
      <p class="muted">Current session</p>
    </div>
  </section>
</div>

<style>
  .stack {
    display: grid;
    gap: 24px;
    font-family: var(--sans);
  }
  h2 {
    font-size: 18px;
  }
  .card > h2 {
    padding: 22px 24px;
  }
  form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 24px;
    border-top: 1px solid #e5eded;
  }
  .wide {
    grid-column: 1 / -1;
  }
  form button {
    grid-column: 2;
    justify-self: end;
    border-radius: 12px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card.row {
    padding: 12px 24px 12px 0;
  }
  .sessions {
    padding: 24px;
  }
  .muted {
    margin-top: 4px;
    color: var(--muted);
  }
  .session {
    margin-top: 20px;
    padding: 16px;
    border-radius: 12px;
    background: #f4f8f8;
  }
  .out {
    color: var(--danger);
    border-color: #e0b9b9;
  }
</style>
