<script lang="ts">
  import { analyses } from '#lib/analyses.svelte.ts';
  import Notice from '#lib/components/Notice.svelte';
  import ResultCard from '#lib/components/ResultCard.svelte';
  import Sidebar from '#lib/components/Sidebar.svelte';
  let question = $state('');

  async function submit(event?: Event) {
    event?.preventDefault();
    if (await analyses.ask(question)) question = '';
  }
</script>

<div class="flex h-screen">
  <Sidebar />
  <main class="flex min-w-0 flex-1 flex-col">
    <header class="min-h-[72px] border border-[#adadad] bg-white px-[22px] py-5">
      <h1 class="truncate text-[26.5px]">{analyses.active?.title ?? 'New analysis'}</h1>
    </header>
    <div
      class="flex flex-1 flex-col gap-[25px] overflow-y-auto pt-[58px] pr-[25px] pb-[25px] pl-[19px]"
    >
      {#each analyses.active?.results ?? [] as result, index (index)}<ResultCard {result} />{/each}
      {#if !analyses.active && !analyses.pending}
        <p class="m-auto text-[18px] text-body">
          Ask a clinical question across your studies to start an analysis.
        </p>
      {/if}
      {#if analyses.pending}<p role="status">
          {analyses.think ? 'Thinking about' : 'Analysing'} “{analyses.pending}”…
        </p>{/if}
      {#if analyses.error}<Notice role="alert">{analyses.error}</Notice>{/if}
    </div>
    <form
      class="mx-[50px] my-3.5 flex gap-2 rounded-2xl border border-[#cedbdd] bg-white p-2 shadow-[0_12px_35px_#143e451f] has-[textarea:focus-visible]:outline-2 has-[textarea:focus-visible]:outline-link"
      onsubmit={submit}
    >
      <textarea
        class="min-w-0 flex-1 resize-none p-3 outline-none"
        rows="1"
        maxlength="2000"
        aria-label="Ask a question"
        placeholder={analyses.active ? 'Ask another question' : 'Ask a question'}
        disabled={!!analyses.pending}
        bind:value={question}
        onkeydown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) void submit(event);
        }}></textarea>
      <button
        type="button"
        class="rounded-xl border border-field px-3.5 text-body aria-pressed:border-brand aria-pressed:bg-tint aria-pressed:text-brand"
        aria-pressed={analyses.think}
        title="Slower, but better on hard questions"
        disabled={!!analyses.pending}
        onclick={() => (analyses.think = !analyses.think)}
      >
        Thinking
      </button>
      <button
        class="grid size-11 place-items-center rounded-xl bg-action"
        aria-label="Submit question"
        disabled={!!analyses.pending || !question.trim()}
      >
        <img src="/images/submit.svg" alt="" />
      </button>
    </form>
  </main>
</div>
