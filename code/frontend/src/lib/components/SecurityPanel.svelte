<script lang="ts">
  import DemoNotice from './DemoNotice.svelte';
</script>

<div class="stack">
  <DemoNotice />
  <section class="card">
    <h2>Password &amp; authentication</h2>
    <form onsubmit={(event) => event.preventDefault()}>
      <label class="field wide">
        Current password<input
          type="password"
          autocomplete="current-password"
          placeholder="Enter current password"
        />
      </label>
      <label class="field">
        New password<input
          type="password"
          autocomplete="new-password"
          minlength="12"
          placeholder="At least 12 characters"
        />
      </label>
      <label class="field">
        Confirm password<input
          type="password"
          autocomplete="new-password"
          placeholder="Repeat new password"
        />
      </label>
      <button class="btn primary" disabled>Update password</button>
    </form>
  </section>
  <section class="card row">
    <h2>Two-factor authentication</h2>
    <input type="checkbox" role="switch" aria-label="Two-factor authentication" disabled />
  </section>
  <section class="card sessions">
    <div class="row">
      <div>
        <h2>Active sessions</h2>
        <p class="muted">Devices currently signed in to your account.</p>
      </div>
      <button class="btn out" disabled>Sign out others</button>
    </div>
    <div class="session">
      Chrome on PC
      <p class="muted">Current session · London, United Kingdom</p>
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
  input[role='switch'] {
    appearance: none;
    width: 44px;
    height: 24px;
    border-radius: 12px;
    background: #cad7d9 radial-gradient(circle at 12px 12px, #fff 8px, transparent 8.5px);
  }
</style>
