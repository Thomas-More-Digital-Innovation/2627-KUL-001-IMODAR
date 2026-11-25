import { describe, expect, it, vi } from 'vitest';
import { Analyses } from './analyses.svelte';
import type { AnalysisResponse, createAnalysis } from './api/client';

const setup = () => {
  const run = vi
    .fn<typeof createAnalysis>()
    .mockResolvedValue({ status: 'ok' } as AnalysisResponse);
  return { run, store: new Analyses(run) };
};

describe('Analyses', () => {
  it('appends follow-ups and starts new analyses', async () => {
    const { store } = setup();
    await store.ask(' first ');
    await store.ask('follow-up');
    expect(store.items).toHaveLength(1);
    expect(store.active?.results).toHaveLength(2);
    store.select(null);
    await store.ask('second');
    expect(store.items.map((item) => item.title)).toEqual(['second', 'first']);
  });

  it('sends the thinking and graph choices with each question', async () => {
    const { run, store } = setup();
    await store.ask('a');
    store.think = true;
    store.graphs = true;
    await store.ask('b');
    expect(run.mock.calls.map(([body]) => [body.think, body.graphs])).toEqual([
      [false, false],
      [true, true],
    ]);
  });

  it('keeps state unchanged on failure', async () => {
    const { run, store } = setup();
    run.mockRejectedValue(new Error('Offline'));
    expect(await store.ask('x')).toBe(false);
    expect([store.items.length, store.error, store.pending]).toEqual([0, 'Offline', null]);
  });

  it('ignores blank and concurrent questions', async () => {
    const { run, store } = setup();
    await store.ask(' ');
    const first = store.ask('a');
    await store.ask('b');
    await first;
    expect(run).toHaveBeenCalledTimes(1);
  });
});
