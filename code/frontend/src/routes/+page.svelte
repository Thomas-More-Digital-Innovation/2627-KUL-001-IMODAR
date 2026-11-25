<script lang="ts">
  import { analyses } from '#lib/analyses.svelte.ts';
  import ResultCard from '#lib/components/ResultCard.svelte';
  import Sidebar from '#lib/components/Sidebar.svelte';
  let question = $state('');

  async function submit(event?: Event) {
    event?.preventDefault();
    if (await analyses.ask(question)) question = '';
  }
</script>

<div class="layout">
  <Sidebar />
  <main>
    <header><h1>{analyses.active?.title ?? 'New analysis'}</h1></header>
    <div class="results">
      {#each analyses.active?.results ?? [] as result, index (index)}<ResultCard {result} />{/each}
      {#if !analyses.active && !analyses.pending}
        <p class="empty">Ask a clinical question across your studies to start an analysis.</p>
      {/if}
      {#if analyses.pending}<p role="status">Analysing “{analyses.pending}”…</p>{/if}
      {#if analyses.error}<p class="notice" role="alert">{analyses.error}</p>{/if}
    </div>
    <form onsubmit={submit}>
      <textarea
        rows="1"
        maxlength="2000"
        aria-label="Ask a question"
        placeholder={analyses.active ? 'Ask another question' : 'Ask a question'}
        disabled={!!analyses.pending}
        bind:value={question}
        onkeydown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) void submit(event);
        }}></textarea>
      <button aria-label="Submit question" disabled={!!analyses.pending || !question.trim()}>
        <img src="/images/submit.svg" alt="" />
      </button>
    </form>
  </main>
</div>

<style>
  .layout {
    display: flex;
    height: 100vh;
  }
  main {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-width: 0;
  }
  header {
    min-height: 72px;
    padding: 20px 22px;
    border: 1px solid #adadad;
    background: #fff;
  }
  h1 {
    overflow: hidden;
    font-size: 26.5px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .results {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 25px;
    padding: 58px 25px 25px 19px;
    overflow-y: auto;
  }
  .empty {
    margin: auto;
    color: var(--body);
    font-size: 18px;
  }
  form {
    display: flex;
    gap: 8px;
    margin: 14px 50px;
    padding: 8px;
    border: 1px solid #cedbdd;
    border-radius: 16px;
    background: #fff;
    box-shadow: 0 12px 35px #143e451f;
  }
  textarea {
    flex: 1;
    min-width: 0;
    padding: 12px;
    border: 0;
    resize: none;
  }
  form button {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: var(--action);
  }
</style>
