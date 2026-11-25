import { createAnalysis, type AnalysisResponse } from './api/client';

export interface Analysis {
  id: number;
  title: string;
  results: AnalysisResponse[];
}

/** Session-only analysis history. */
// TODO: persist per user once the backend has accounts and storage.
export class Analyses {
  items = $state<Analysis[]>([]);
  activeId = $state<number | null>(null);
  pending = $state<string | null>(null);
  think = $state(false);
  error = $state<string | null>(null);
  active = $derived(this.items.find((item) => item.id === this.activeId) ?? null);
  #nextId = 1;
  #run: typeof createAnalysis;

  constructor(run: typeof createAnalysis = createAnalysis) {
    this.#run = run;
  }

  select(id: number | null): void {
    if (this.pending) return;
    this.activeId = id;
    this.error = null;
  }

  async ask(raw: string): Promise<boolean> {
    const question = raw.trim();
    if (!question || this.pending) return false;
    this.pending = question;
    this.error = null;
    try {
      const result = await this.#run({ question, think: this.think });
      if (this.active) {
        this.active.results.push(result);
      } else {
        const id = this.#nextId++;
        this.items.unshift({ id, title: question, results: [result] });
        this.activeId = id;
      }
      return true;
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'The analysis could not be completed.';
      return false;
    } finally {
      this.pending = null;
    }
  }
}

export const analyses = new Analyses();
