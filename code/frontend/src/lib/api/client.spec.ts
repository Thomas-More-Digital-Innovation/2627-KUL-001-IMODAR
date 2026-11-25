import { describe, expect, it, vi } from 'vitest';
import { createAnalysis } from './client';

describe('createAnalysis', () => {
  it('posts the question', async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json({ status: 'ok' }));
    await createAnalysis('How many?', fetcher);
    expect(fetcher).toHaveBeenCalledWith(
      '/api/analyses',
      expect.objectContaining({ method: 'POST', body: '{"question":"How many?"}' }),
    );
  });

  it.each([
    [Response.json({ detail: 'Offline' }, { status: 503 }), 'Offline'],
    [Response.json({ detail: [{ msg: 'x' }] }, { status: 422 }), 'could not be completed'],
    [new Response('<html>', { status: 500 }), 'could not be completed'],
  ])('reports failures', async (response, message) => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response);
    await expect(createAnalysis('x', fetcher)).rejects.toThrow(message);
  });
});
