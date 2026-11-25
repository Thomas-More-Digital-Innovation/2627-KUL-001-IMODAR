import { describe, expect, it, vi } from 'vitest';
import { createAnalysis } from './client';

describe('createAnalysis', () => {
  it('posts the question', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ status: 'ok' }));
    await createAnalysis({ question: 'How many?', think: true, graphs: true }, fetcher);
    expect(fetcher).toHaveBeenCalledWith(
      '/api/analyses',
      expect.objectContaining({
        method: 'POST',
        body: '{"question":"How many?","think":true,"graphs":true}',
      }),
    );
  });

  it.each([
    [Response.json({ detail: 'Offline' }, { status: 503 }), 'Offline'],
    [Response.json({ detail: [{ msg: 'x' }] }, { status: 422 }), 'could not be completed'],
    [new Response('<html>', { status: 500 }), 'could not be completed'],
  ])('reports failures', async (response, message) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response);
    await expect(createAnalysis({ question: 'x', graphs: false }, fetcher)).rejects.toThrow(
      message,
    );
  });
});
