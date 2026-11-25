<script lang="ts">
  let submitted = $state(false);
</script>

<svelte:head><title>Sign in · IMODAR</title></svelte:head>
<main>
  <div class="art"><img src="/images/dna.png" alt="" /><span class="logo">IMODAR</span></div>
  <form
    onsubmit={(event) => {
      event.preventDefault();
      submitted = true;
    }}
  >
    <h1>IMODAR</h1>
    <p class="subtitle">Sign in to your workspace</p>
    <label class="field">
      Email address<input
        type="email"
        autocomplete="username"
        placeholder="example@example.com"
        required
      />
    </label>
    <label class="field">
      Password<input type="password" autocomplete="current-password" required />
    </label>
    <div class="options">
      <label><input type="checkbox" /> Remember me</label>
      <button type="button" class="link" disabled>Forgot password?</button>
    </div>
    <button class="submit">Sign in <img src="/images/arrow.svg" alt="" /></button>
    {#if submitted}
      <!-- TODO: replace with a real session once the backend provides authentication. -->
      <p class="notice" role="status">
        Sign-in is not connected yet. <a class="link" href="/">Continue to workspace</a>
      </p>
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
  @media (max-width: 800px) {
    main {
      grid-template-columns: 1fr;
    }
    .art {
      display: none;
    }
  }
</style>
