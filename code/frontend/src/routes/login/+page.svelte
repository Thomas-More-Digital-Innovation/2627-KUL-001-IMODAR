<script lang="ts">
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';
  import SignInCode from '#lib/components/SignInCode.svelte';

  let step = $state<'password' | 'verify' | 'enrol' | 'codes'>('password');
  let email = $state('');
  let password = $state('');
  let remember = $state(false);
  let code = $state('');
  let enrolment = $state({ secret: '', qr_code: '' });
  let recoveryCodes = $state<string[]>([]);
  let busy = $state(false);
  let error = $state('');

  const subtitle = $derived(
    {
      password: 'Sign in to your workspace',
      verify: 'Two-factor authentication',
      enrol: 'Set up two-factor authentication',
      codes: 'Save your recovery codes',
    }[step],
  );

  function enterWorkspace() {
    // A full load guarantees no state from a previous user survives in memory.
    window.location.assign('/');
  }

  async function advance() {
    if (step === 'password') {
      const { next } = await auth.login({ email, password, remember });
      password = '';
      if (next === 'enrol') enrolment = await auth.enrol();
      step = next;
    } else if (step === 'verify') {
      await auth.verify(code);
      enterWorkspace();
    } else if (step === 'enrol') {
      recoveryCodes = (await auth.confirm(code)).recovery_codes;
      step = 'codes';
    } else {
      enterWorkspace();
    }
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    busy = true;
    error = '';
    try {
      await advance();
    } catch (cause) {
      error = messageOf(cause);
    } finally {
      code = '';
      busy = false;
    }
  }

  function restart() {
    step = 'password';
    error = '';
  }
</script>

<svelte:head><title>Sign in · IMODAR</title></svelte:head>
<main>
  <div class="art"><img src="/images/dna.png" alt="" /><span class="logo">IMODAR</span></div>
  <form onsubmit={submit}>
    <h1>IMODAR</h1>
    <p class="subtitle">{subtitle}</p>
    {#if step === 'password'}
      <label class="field">
        Email address
        <input
          type="email"
          autocomplete="username"
          placeholder="example@example.com"
          required
          bind:value={email}
        />
      </label>
      <label class="field">
        Password
        <input
          type="password"
          autocomplete="current-password"
          maxlength="128"
          required
          bind:value={password}
        />
      </label>
      <div class="options">
        <label><input type="checkbox" bind:checked={remember} /> Remember me</label>
        <!-- TODO: enable once password reset emails exist. -->
        <button type="button" class="link" disabled>Forgot password?</button>
      </div>
    {:else if step === 'verify'}
      <SignInCode label="Authenticator or recovery code" bind:code />
    {:else if step === 'enrol'}
      <p class="enrol">Scan this with your authenticator app, then enter the code it shows.</p>
      <img class="qr" src={enrolment.qr_code} alt="QR code for your authenticator app" />
      <p class="enrol">Or enter this key: <code>{enrolment.secret}</code></p>
      <SignInCode label="Authenticator code" bind:code />
    {:else}
      <p class="enrol">
        Each code replaces your authenticator once. Store them safely; they are not shown again.
      </p>
      <ul class="codes">
        {#each recoveryCodes as item (item)}<li><code>{item}</code></li>{/each}
      </ul>
    {/if}
    {#if error}<p class="notice" role="alert">{error}</p>{/if}
    <button class="submit" disabled={busy}>
      {step === 'password' ? 'Sign in' : step === 'codes' ? 'I saved these codes' : 'Verify'}
      <img src="/images/arrow.svg" alt="" />
    </button>
    {#if step === 'verify' || step === 'enrol'}
      <button type="button" class="link" onclick={restart}>Start again</button>
    {/if}
  </form>
</main>

<style>
  main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    min-height: 100vh;
  }
  .art {
    position: relative;
    overflow: hidden;
    background: var(--navy);
  }
  .art img {
    position: absolute;
    top: -2.5%;
    left: -23.6%;
    width: 156.4%;
    max-width: none;
    transform: rotate(-85.85deg);
    transform-origin: 52.3% 47.8%;
  }
  .art span {
    position: absolute;
    top: 18px;
    left: 24px;
    color: #fff;
  }
  form {
    display: grid;
    align-content: start;
    gap: 27px;
    width: min(620px, 86%);
    margin: 137px auto 40px;
  }
  h1 {
    font-size: 64px;
    font-weight: 800;
    line-height: 70px;
    text-align: center;
    color: #000;
  }
  .subtitle {
    margin: -27px 0 28px;
    font-size: 36px;
    letter-spacing: -1.26px;
    text-align: center;
  }
  .field,
  .options {
    font-size: 19.3px;
  }
  .field input {
    height: 77px;
    padding: 0 21px;
    border-radius: 16.5px;
    font-size: 22px;
  }
  .options,
  .options label {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    color: var(--body);
  }
  .submit {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 11px;
    height: 77px;
    border-radius: 16.5px;
    background: var(--action);
    color: #fff;
    font-size: 22px;
    box-shadow: 0 10px 20px #087f9133;
  }
  .enrol {
    font-size: 16px;
    line-height: 24px;
  }
  .qr {
    width: 220px;
    margin: 0 auto;
    background: #fff;
  }
  code {
    overflow-wrap: anywhere;
  }
  .codes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 0;
    padding: 20px;
    border-radius: 12px;
    background: #fff;
    list-style: none;
  }
  @media (max-width: 800px) {
    main {
      grid-template-columns: 1fr;
    }
    .art {
      display: none;
    }
  }
</style>
