<script lang="ts">
  import { auth } from '#lib/api/auth.ts';
  import { messageOf } from '#lib/api/http.ts';
  import Button from '#lib/components/Button.svelte';
  import Field from '#lib/components/Field.svelte';
  import Logo from '#lib/components/Logo.svelte';
  import Notice from '#lib/components/Notice.svelte';
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
<main class="grid min-h-screen grid-cols-2 max-[801px]:grid-cols-1">
  <div class="relative overflow-hidden bg-navy max-[801px]:hidden">
    <img
      class="absolute top-[-2.5%] left-[-23.6%] w-[156.4%] max-w-none origin-[52.3%_47.8%] rotate-[-85.85deg]"
      src="/images/dna.png"
      alt=""
    />
    <Logo class="absolute top-[18px] left-6 text-white" />
  </div>
  <form
    class="mx-auto mt-[137px] mb-10 grid w-[min(620px,86%)] content-start gap-[27px]"
    onsubmit={submit}
  >
    <h1 class="text-center text-[64px] leading-[70px] font-extrabold text-black">IMODAR</h1>
    <p class="-mt-[27px] mb-7 text-center text-[36px] tracking-[-1.26px]">{subtitle}</p>
    {#if step === 'password'}
      <Field label="Email address" large>
        <input
          type="email"
          autocomplete="username"
          placeholder="example@example.com"
          required
          bind:value={email}
        />
      </Field>
      <Field label="Password" large>
        <input
          type="password"
          autocomplete="current-password"
          maxlength="128"
          required
          bind:value={password}
        />
      </Field>
      <div class="flex items-center justify-between gap-3.5 text-[19.3px] text-body">
        <label class="flex items-center gap-3.5">
          <input type="checkbox" bind:checked={remember} /> Remember me
        </label>
        <!-- TODO: enable once password reset emails exist. -->
        <Button type="button" variant="link" disabled>Forgot password?</Button>
      </div>
    {:else if step === 'verify'}
      <SignInCode label="Authenticator or recovery code" bind:code />
    {:else if step === 'enrol'}
      <p class="text-[16px] leading-6">
        Scan this with your authenticator app, then enter the code it shows.
      </p>
      <img
        class="mx-auto w-[220px] bg-white"
        src={enrolment.qr_code}
        alt="QR code for your authenticator app"
      />
      <p class="text-[16px] leading-6">
        Or enter this key: <code class="text-[13px] wrap-anywhere">{enrolment.secret}</code>
      </p>
      <SignInCode label="Authenticator code" bind:code />
    {:else}
      <p class="text-[16px] leading-6">
        Each code replaces your authenticator once. Store them safely; they are not shown again.
      </p>
      <ul class="grid grid-cols-2 gap-2 rounded-xl bg-white p-5">
        {#each recoveryCodes as item (item)}<li>
            <code class="text-[13px] wrap-anywhere">{item}</code>
          </li>{/each}
      </ul>
    {/if}
    {#if error}<Notice role="alert">{error}</Notice>{/if}
    <button
      class="flex h-[77px] items-center justify-center gap-[11px] rounded-[16.5px] bg-action text-[22px] text-white shadow-[0_10px_20px_#087f9133]"
      disabled={busy}
    >
      {step === 'password' ? 'Sign in' : step === 'codes' ? 'I saved these codes' : 'Verify'}
      <img src="/images/arrow.svg" alt="" />
    </button>
    {#if step === 'verify' || step === 'enrol'}
      <Button type="button" variant="link" onclick={restart}>Start again</Button>
    {/if}
  </form>
</main>
