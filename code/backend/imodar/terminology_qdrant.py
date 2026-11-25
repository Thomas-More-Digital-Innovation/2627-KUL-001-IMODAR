"""Qdrant Vector Store with BGE-M3 for Multilingual OMOP Concept Resolution."""

from __future__ import annotations

import time
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models

from . import config
from .engine import Warehouse

VECTOR_DIM = 1024  # bge-m3 embedding dimension


class QdrantConceptStore:
    def __init__(
        self,
        qdrant_url: str = config.QDRANT_URL,
        collection_name: str = config.QDRANT_COLLECTION,
        ollama_url: str = config.OLLAMA_URL,
        embedding_model: str = config.EMBEDDING_MODEL,
        auto_init_warehouse: Warehouse | None = None,
    ):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.ollama_url = ollama_url.rstrip("/")
        self.embedding_model = embedding_model
        self.client = QdrantClient(url=self.qdrant_url, timeout=10.0)
        self._http = httpx.Client(base_url=self.ollama_url, timeout=30.0)

        # Check / create collection
        self._ensure_collection()

        # Auto-index if collection is empty and warehouse provided
        if auto_init_warehouse and self.count() == 0:
            self.index_warehouse(auto_init_warehouse)

    def is_alive(self) -> bool:
        try:
            r = self._http.get("/api/tags", timeout=3.0)
            if r.status_code != 200:
                return False
            self.client.get_collections()
            return True
        except Exception:
            return False

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIM,
                    distance=models.Distance.COSINE,
                ),
            )

    def count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding via Ollama /api/embed."""
        if not texts:
            return []
        try:
            resp = self._http.post(
                "/api/embed",
                json={"model": self.embedding_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("embeddings", [])
        except Exception as e:
            raise RuntimeError(f"Ollama embedding failed ({self.embedding_model}): {e}") from e

    def embed_single(self, text: str) -> list[float]:
        vectors = self.embed_batch([text])
        if not vectors:
            raise ValueError(f"No vector returned for: {text}")
        return vectors[0]

    def index_warehouse(self, wh: Warehouse, batch_size: int = 50) -> int:
        """Indexes concepts, synonyms, and categorical values from DuckDB into Qdrant."""
        t0 = time.time()
        print(
            f"Indexing OMOP concepts & categorical values into Qdrant ({self.collection_name}) using {self.embedding_model}..."
        )

        # 1. Fetch concepts & synonyms
        # By default, vector-index active clinical concepts (OncoTree, study concepts, covered concepts).
        # RapidFuzz and SQL handle the full 100k+ reference catalog (NCIt, MONDO) instantly.
        if getattr(config, "QDRANT_INDEX_ALL", False):
            c_df = wh.query_df("SELECT concept_id, concept_name, domain_id, concept_code FROM omop.concept")
            s_df = wh.query_df("SELECT concept_id, concept_synonym_name FROM omop.concept_synonym")
        else:
            c_df = wh.query_df("""
                SELECT concept_id, concept_name, domain_id, concept_code 
                FROM omop.concept
                WHERE vocabulary_id IN ('OncoTree', 'IMO_LOCAL', 'Gender')
                   OR concept_id IN (SELECT concept_id FROM catalog.concept_coverage)
            """)
            s_df = wh.query_df("""
                SELECT s.concept_id, s.concept_synonym_name 
                FROM omop.concept_synonym s
                JOIN omop.concept c ON c.concept_id = s.concept_id
                WHERE c.vocabulary_id IN ('OncoTree', 'IMO_LOCAL', 'Gender')
                   OR c.concept_id IN (SELECT concept_id FROM catalog.concept_coverage)
            """)

        items_to_embed: list[dict[str, Any]] = []

        for r in c_df.itertuples():
            cid = int(r.concept_id)
            items_to_embed.append(
                {
                    "text": str(r.concept_name),
                    "payload": {
                        "kind": "concept",
                        "concept_id": cid,
                        "concept_name": str(r.concept_name),
                        "domain_id": str(r.domain_id),
                        "matched_text": str(r.concept_name),
                    },
                }
            )
            if r.concept_code and r.concept_code != r.concept_name:
                items_to_embed.append(
                    {
                        "text": str(r.concept_code),
                        "payload": {
                            "kind": "concept",
                            "concept_id": cid,
                            "concept_name": str(r.concept_name),
                            "domain_id": str(r.domain_id),
                            "matched_text": str(r.concept_code),
                        },
                    }
                )

        for r in s_df.itertuples():
            cid = int(r.concept_id)
            concept_meta = c_df[c_df.concept_id == cid]
            name = concept_meta.concept_name.iloc[0] if len(concept_meta) else str(cid)
            domain = concept_meta.domain_id.iloc[0] if len(concept_meta) else "Unknown"
            items_to_embed.append(
                {
                    "text": str(r.concept_synonym_name),
                    "payload": {
                        "kind": "concept",
                        "concept_id": cid,
                        "concept_name": name,
                        "domain_id": domain,
                        "matched_text": str(r.concept_synonym_name),
                    },
                }
            )

        # 2. Fetch distinct categorical values
        for col in ("gene_symbol", "variant_type", "cnv_status", "fusion_gene", "ngs_panel"):
            for v in wh.query_df(f"SELECT DISTINCT {col} AS v FROM genomics.ngs_variant WHERE {col} IS NOT NULL").v:
                items_to_embed.append(
                    {
                        "text": str(v),
                        "payload": {
                            "kind": "value",
                            "table_column": f"genomics.ngs_variant.{col}",
                            "value": str(v),
                            "concept_id": None,
                            "matched_text": str(v),
                        },
                    }
                )

        for r in wh.query_df(
            "SELECT DISTINCT observation_concept_id cid, value_as_string v, value_source_value s FROM omop.observation"
        ).itertuples():
            items_to_embed.append(
                {
                    "text": str(r.v),
                    "payload": {
                        "kind": "value",
                        "table_column": "omop.observation.value_as_string",
                        "value": str(r.v),
                        "concept_id": int(r.cid),
                        "matched_text": str(r.v),
                    },
                }
            )
            if r.s and r.s != r.v:
                items_to_embed.append(
                    {
                        "text": str(r.s),
                        "payload": {
                            "kind": "value",
                            "table_column": "omop.observation.value_as_string",
                            "value": str(r.v),
                            "concept_id": int(r.cid),
                            "matched_text": str(r.s),
                        },
                    }
                )

        for v in wh.query_df("SELECT DISTINCT specimen_type v FROM omop.specimen WHERE specimen_type IS NOT NULL").v:
            items_to_embed.append(
                {
                    "text": str(v),
                    "payload": {
                        "kind": "value",
                        "table_column": "omop.specimen.specimen_type",
                        "value": str(v),
                        "concept_id": None,
                        "matched_text": str(v),
                    },
                }
            )

        for v in wh.query_df("SELECT DISTINCT timepoint v FROM omop.measurement WHERE timepoint IS NOT NULL").v:
            items_to_embed.append(
                {
                    "text": str(v),
                    "payload": {
                        "kind": "value",
                        "table_column": "omop.measurement.timepoint",
                        "value": str(v),
                        "concept_id": None,
                        "matched_text": str(v),
                    },
                }
            )

        # Deduplicate texts with same payload
        deduped = []
        seen = set()
        for it in items_to_embed:
            k = (
                it["text"].strip().lower(),
                it["payload"]["kind"],
                it["payload"].get("concept_id"),
                it["payload"].get("table_column"),
                it["payload"].get("value"),
            )
            if k not in seen:
                seen.add(k)
                deduped.append(it)

        # Recreate collection cleanly before indexing
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._ensure_collection()

        # Batch embed and stream upload to Qdrant in chunks of 100 points (keeps payloads < 2MB)
        point_id = 1
        total_points = 0
        points_buffer: list[models.PointStruct] = []
        UPSERT_CHUNK_SIZE = 100

        for i in range(0, len(deduped), batch_size):
            chunk = deduped[i : i + batch_size]
            texts = [c["text"] for c in chunk]
            vectors = self.embed_batch(texts)
            for item, vec in zip(chunk, vectors, strict=True):
                points_buffer.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vec,
                        payload=item["payload"],
                    )
                )
                point_id += 1

            if len(points_buffer) >= UPSERT_CHUNK_SIZE:
                self.client.upsert(collection_name=self.collection_name, points=points_buffer)
                total_points += len(points_buffer)
                points_buffer = []

        if points_buffer:
            self.client.upsert(collection_name=self.collection_name, points=points_buffer)
            total_points += len(points_buffer)

        elapsed = time.time() - t0
        print(f"Indexed {total_points} points into Qdrant in {elapsed:.1f}s.")
        return total_points

    def search_concepts(self, text: str, k: int = 3, score_threshold: float = 0.55) -> list[dict[str, Any]]:
        """Semantic search against OMOP concepts."""
        vec = self.embed_single(text)
        res = self.client.query_points(
            collection_name=self.collection_name,
            query=vec,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="kind",
                        match=models.MatchValue(value="concept"),
                    )
                ]
            ),
            limit=k * 3,
            score_threshold=score_threshold,
        )

        seen_concepts = set()
        hits = []
        for p in res.points:
            cid = p.payload["concept_id"]
            if cid not in seen_concepts:
                seen_concepts.add(cid)
                hits.append(
                    {
                        "concept_id": cid,
                        "concept_name": p.payload["concept_name"],
                        "domain_id": p.payload["domain_id"],
                        "matched_on": p.payload["matched_text"],
                        "score": round(float(p.score) * 100, 1),
                    }
                )
            if len(hits) >= k:
                break
        return hits

    def search_values(self, text: str, k: int = 5, score_threshold: float = 0.60) -> list[dict[str, Any]]:
        """Semantic search against categorical column values."""
        vec = self.embed_single(text)
        res = self.client.query_points(
            collection_name=self.collection_name,
            query=vec,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="kind",
                        match=models.MatchValue(value="value"),
                    )
                ]
            ),
            limit=k * 2,
            score_threshold=score_threshold,
        )

        seen = set()
        hits = []
        for p in res.points:
            key = (p.payload["table_column"], p.payload["value"])
            if key not in seen:
                seen.add(key)
                hits.append(
                    {
                        "table_column": p.payload["table_column"],
                        "value": p.payload["value"],
                        "concept_id": p.payload.get("concept_id"),
                        "matched_on": p.payload["matched_text"],
                        "score": round(float(p.score) * 100, 1),
                    }
                )
            if len(hits) >= k:
                break
        return hits
