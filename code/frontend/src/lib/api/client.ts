import type { components } from './schema';

export type AnalysisResponse = components['schemas']['AnalysisResponse'];
export type ResultTable = components['schemas']['ResultTable'];

/** Runs a question through the audited analysis pipeline. */
export async function createAnalysis(
  question: string,
  fetcher: typeof fetch = fetch,
): Promise<AnalysisResponse> {
  const response = await fetcher('/api/analyses', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : 'The analysis could not be completed.';
    throw new Error(detail);
  }
  return response.json();
}
