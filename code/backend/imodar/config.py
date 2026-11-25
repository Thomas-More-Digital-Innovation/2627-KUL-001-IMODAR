"""Runtime configuration (overridable through environment variables)."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE_DIR = Path(os.getenv("IMODAR_WAREHOUSE", str(PROJECT_ROOT / "warehouse")))
DB_PATH = WAREHOUSE_DIR / "imodar.duckdb"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.8:27b")
OLLAMA_TIMEOUT_S = float(os.getenv("OLLAMA_TIMEOUT_S", "300"))
# Thinking improves SQL on hard questions but is slower; toggle in the UI.
OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").lower() == "true"

# Semantic vector search (Qdrant + bge-m3)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "omop_concepts")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")
USE_QDRANT = os.getenv("USE_QDRANT", "true").lower() == "true"

MAX_RESULT_ROWS = int(os.getenv("IMODAR_MAX_ROWS", "5000"))
QUERY_TIMEOUT_S = float(os.getenv("IMODAR_QUERY_TIMEOUT_S", "30"))
MAX_PLAN_ATTEMPTS = int(os.getenv("IMODAR_MAX_ATTEMPTS", "3"))
SYNTH_MAX_ROWS = int(os.getenv("IMODAR_SYNTH_MAX_ROWS", "60"))
