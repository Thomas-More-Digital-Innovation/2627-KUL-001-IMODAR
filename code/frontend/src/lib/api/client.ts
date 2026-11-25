import { json, request } from './http.ts';
import type { components } from './schema';

type Schemas = components['schemas'];
export type AnalysisResponse = Schemas['AnalysisResponse'];
export type ResultTable = Schemas['ResultTable'];

/** Runs a question through the audited analysis pipeline. */
export async function createAnalysis(
  body: Schemas['AnalysisRequest'],
  fetcher: typeof fetch = fetch,
): Promise<AnalysisResponse> {
  const fallback = 'The analysis could not be completed.';
  return (await request('/api/analyses', fallback, json(body), fetcher)).json();
}
