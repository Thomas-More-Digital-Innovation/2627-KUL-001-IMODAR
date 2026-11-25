"""Semantic entity resolution: free-text mentions -> concept IDs / exact categorical values.

The LLM never invents concept IDs. It may *extract* mentions from the question; this module
deterministically maps them to concepts that exist in the warehouse:
  1. Exact matching on concept codes, names, HGNC symbols, and categorical values.
  2. Semantic vector search in Qdrant powered by BGE-M3.

Fuzzy finding is strictly disabled. If Qdrant is offline or unreachable, an explicit
RuntimeError is raised immediately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config
from .engine import Warehouse


@dataclass
class ConceptHit:
    concept_id: int
    concept_name: str
    domain_id: str
    matched_on: str
    score: float
    coverage: list[dict] = field(default_factory=list)  # per study: table, n_persons, units, value_types
    values: list[str] = field(default_factory=list)  # observation value set
    descendants: list[tuple[int, str]] = field(default_factory=list)
    source: str = "qdrant_bge_m3"  # 'qdrant_bge_m3' | 'exact'


@dataclass
class ValueHit:
    table_column: str  # e.g. genomics.ngs_variant.gene_symbol | omop.observation.value_as_string
    value: str
    concept_id: int | None
    concept_name: str | None
    matched_on: str
    score: float
    source: str = "qdrant_bge_m3"  # 'qdrant_bge_m3' | 'exact'


@dataclass
class Resolution:
    mention: str
    concepts: list[ConceptHit] = field(default_factory=list)
    values: list[ValueHit] = field(default_factory=list)


class ConceptIndex:
    def __init__(self, wh: Warehouse, use_qdrant: bool = True):
        self.wh = wh

        # Qdrant is strictly required. If offline, crash immediately.
        from .terminology_qdrant import QdrantConceptStore

        try:
            store = QdrantConceptStore(qdrant_url=config.QDRANT_URL, auto_init_warehouse=wh)
            if not store.is_alive():
                raise RuntimeError(
                    f"Qdrant vector store at '{config.QDRANT_URL}' is offline or unreachable. "
                    "Qdrant is strictly required for semantic entity resolution. Please ensure Qdrant is running."
                )
        except Exception as e:
            raise RuntimeError(
                f"Qdrant vector store at '{config.QDRANT_URL}' is offline or unreachable ({e}). "
                "Qdrant is strictly required for semantic entity resolution. Please ensure Qdrant is running."
            ) from e
        self.qdrant_store = store

        # 1. Load concepts and coverage
        c = wh.query_df("SELECT concept_id, concept_name, domain_id, concept_code FROM omop.concept")
        s = wh.query_df("SELECT concept_id, concept_synonym_name FROM omop.concept_synonym")
        self.concepts = {int(r.concept_id): r for r in c.itertuples()}

        cov = wh.query_df("SELECT * FROM catalog.concept_coverage")
        self.coverage: dict[int, list[dict]] = {}
        for r in cov.to_dict("records"):
            self.coverage.setdefault(int(r["concept_id"]), []).append(
                {k: r[k] for k in ("study_id", "source_table", "modality", "value_types", "units", "n_persons")}
            )

        # 2. Exact match dictionary for codes, names, and synonyms
        self.exact_lookup: dict[str, list[int]] = {}
        for r in c.itertuples():
            cid = int(r.concept_id)
            if r.concept_code:
                self.exact_lookup.setdefault(r.concept_code.strip().lower(), []).append(cid)
            if r.concept_name:
                self.exact_lookup.setdefault(r.concept_name.strip().lower(), []).append(cid)
        for r in s.itertuples():
            cid = int(r.concept_id)
            if r.concept_synonym_name:
                self.exact_lookup.setdefault(r.concept_synonym_name.strip().lower(), []).append(cid)

        # Prioritize concepts with study coverage in exact lookup
        for key in self.exact_lookup:
            self.exact_lookup[key].sort(key=lambda cid: (len(self.coverage.get(cid, [])) > 0, -cid), reverse=True)

        # 3. Categorical value exact lookup
        self.exact_value_lookup: dict[str, list[dict]] = {}
        for col in ("gene_symbol", "variant_type", "cnv_status", "fusion_gene", "ngs_panel"):
            for v in wh.query_df(f"SELECT DISTINCT {col} AS v FROM genomics.ngs_variant WHERE {col} IS NOT NULL").v:
                item = {
                    "table_column": f"genomics.ngs_variant.{col}",
                    "value": str(v),
                    "concept_id": None,
                    "concept_name": None,
                }
                self.exact_value_lookup.setdefault(str(v).strip().lower(), []).append(item)
        for r in wh.query_df(
            "SELECT DISTINCT observation_concept_id cid, value_as_string v, value_source_value s FROM omop.observation"
        ).itertuples():
            cid = int(r.cid)
            c_name = self.concepts[cid].concept_name if cid in self.concepts else None
            item = {
                "table_column": "omop.observation.value_as_string",
                "value": str(r.v),
                "concept_id": cid,
                "concept_name": c_name,
            }
            self.exact_value_lookup.setdefault(str(r.v).strip().lower(), []).append(item)
            if r.s and r.s != r.v:
                self.exact_value_lookup.setdefault(str(r.s).strip().lower(), []).append(item)
        for v in wh.query_df("SELECT DISTINCT specimen_type v FROM omop.specimen WHERE specimen_type IS NOT NULL").v:
            item = {
                "table_column": "omop.specimen.specimen_type",
                "value": str(v),
                "concept_id": None,
                "concept_name": None,
            }
            self.exact_value_lookup.setdefault(str(v).strip().lower(), []).append(item)
        for v in wh.query_df("SELECT DISTINCT timepoint v FROM omop.measurement WHERE timepoint IS NOT NULL").v:
            item = {
                "table_column": "omop.measurement.timepoint",
                "value": str(v),
                "concept_id": None,
                "concept_name": None,
            }
            self.exact_value_lookup.setdefault(str(v).strip().lower(), []).append(item)

        # 4. Observation value sets and hierarchies
        vals = wh.query_df(
            "SELECT observation_concept_id AS cid, value_as_string AS v, count(*) n "
            "FROM omop.observation GROUP BY ALL ORDER BY cid, n DESC"
        )
        self.obs_values: dict[int, list[str]] = {}
        for r in vals.itertuples():
            self.obs_values.setdefault(int(r.cid), []).append(r.v)

        desc = wh.query_df("""SELECT a.ancestor_concept_id AS a, a.descendant_concept_id AS d, c.concept_name AS n
                              FROM omop.concept_ancestor a JOIN omop.concept c ON c.concept_id = a.descendant_concept_id
                              WHERE a.min_levels_of_separation > 0""")
        self.descendants: dict[int, list[tuple[int, str]]] = {}
        for r in desc.itertuples():
            self.descendants.setdefault(int(r.a), []).append((int(r.d), r.n))

    def search(self, term: str, k: int = 3, domain: str | None = None) -> list[ConceptHit]:
        """Resolves term via Exact Match or Qdrant Semantic Search (no fuzzy fallback)."""
        hits: list[ConceptHit] = []

        # 1. Exact match (instant O(1) resolution for codes, symbols, exact concept names)
        norm = term.strip().lower()
        if norm in self.exact_lookup:
            for cid in self.exact_lookup[norm][:k]:
                c = self.concepts.get(cid)
                if c and (not domain or c.domain_id == domain):
                    hits.append(
                        ConceptHit(
                            concept_id=cid,
                            concept_name=c.concept_name,
                            domain_id=c.domain_id,
                            matched_on=term.strip(),
                            score=100.0,
                            source="exact",
                        )
                    )

        # 2. Semantic Vector Search in Qdrant with BGE-M3
        if not hits:
            q_hits = self.qdrant_store.search_concepts(term, k=k, score_threshold=0.60)
            for qh in q_hits:
                cid = qh["concept_id"]
                c = self.concepts.get(cid)
                if domain and c and c.domain_id != domain:
                    continue
                hits.append(
                    ConceptHit(
                        concept_id=cid,
                        concept_name=qh["concept_name"],
                        domain_id=qh["domain_id"],
                        matched_on=qh["matched_on"],
                        score=qh["score"],
                        source="qdrant_bge_m3",
                    )
                )

        # Attach coverage, observation value sets, and descendants
        for h in hits:
            h.coverage = self.coverage.get(h.concept_id, [])
            h.values = self.obs_values.get(h.concept_id, [])[:30]
            h.descendants = self.descendants.get(h.concept_id, [])
        return hits

    def search_values(self, term: str, k: int = 5) -> list[ValueHit]:
        """Resolves categorical value mentions via Exact Match or Qdrant (no fuzzy fallback)."""
        hits: list[ValueHit] = []

        # 1. Exact match for categorical values
        norm = term.strip().lower()
        if norm in self.exact_value_lookup:
            for vh in self.exact_value_lookup[norm][:k]:
                hits.append(
                    ValueHit(
                        table_column=vh["table_column"],
                        value=vh["value"],
                        concept_id=vh["concept_id"],
                        concept_name=vh["concept_name"],
                        matched_on=term.strip(),
                        score=100.0,
                        source="exact",
                    )
                )

        # 2. Semantic Vector Search in Qdrant with BGE-M3
        if not hits:
            q_hits = self.qdrant_store.search_values(term, k=k, score_threshold=0.65)
            for qh in q_hits:
                cid = qh.get("concept_id")
                c_name = self.concepts[cid].concept_name if cid and cid in self.concepts else None
                hits.append(
                    ValueHit(
                        table_column=qh["table_column"],
                        value=qh["value"],
                        concept_id=cid,
                        concept_name=c_name,
                        matched_on=qh["matched_on"],
                        score=qh["score"],
                        source="qdrant_bge_m3",
                    )
                )

        return hits

    def resolve(self, mentions: list[str]) -> list[Resolution]:
        seen, res = set(), []
        for m in mentions:
            m = m.strip()
            if not m or m.lower() in seen:
                continue
            seen.add(m.lower())
            r = Resolution(m, self.search(m), self.search_values(m))
            res.append(r)
        return res


_STOP = set(
    [
        "a",
        "an",
        "the",
        "of",
        "in",
        "on",
        "at",
        "for",
        "to",
        "by",
        "with",
        "and",
        "or",
        "not",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "how",
        "many",
        "much",
        "per",
        "vs",
        "versus",
        "between",
        "from",
        "than",
        "that",
        "this",
        "these",
        "those",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "show",
        "list",
        "give",
        "me",
        "all",
        "any",
        "each",
        "average",
        "mean",
        "median",
        "count",
        "number",
        "patients",
        "patient",
        "study",
        "studies",
        "level",
        "levels",
        "value",
        "values",
        "compare",
        "where",
        "when",
        "there",
        "their",
        "them",
        "it",
        "its",
        "as",
        "into",
        "over",
        "under",
        "more",
        "less",
        "higher",
        "lower",
        "top",
        "most",
        "least",
        "than",
        "about",
        "across",
        "data",
        "table",
        "rows",
        "sample",
        "samples",
        "group",
        "groups",
        "enrolled",
        "enrolling",
    ]
)

_GLUE_START = {
    "are",
    "is",
    "was",
    "were",
    "in",
    "on",
    "at",
    "for",
    "to",
    "by",
    "with",
    "and",
    "or",
    "of",
    "each",
    "every",
    "all",
    "how",
    "what",
    "which",
    "enrolled",
}
_GLUE_END = {"are", "is", "was", "were", "in", "on", "at", "for", "to", "by", "with", "and", "or", "of"}


def candidate_mentions(question: str) -> list[str]:
    """Extract candidate medical entity mentions from question without grammatical noise."""
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/+]*", question)
    grams = []
    for n in (3, 2, 1):
        for i in range(len(toks) - n + 1):
            chunk = toks[i : i + n]
            # Don't create n-grams where all words are stop words
            if all(t.lower() in _STOP for t in chunk):
                continue
            # For multi-word n-grams, skip if it starts or ends with grammatical glue
            if n > 1 and (chunk[0].lower() in _GLUE_START or chunk[-1].lower() in _GLUE_END):
                continue
            g = " ".join(chunk)
            if n == 1 and (len(g) < 2 or g.lower() in _STOP):
                continue
            grams.append(g)
    return grams
