"""Read-only DuckDB execution engine with timeouts and an execution trace."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

from . import config

QUERYABLE_SCHEMAS = ("omop", "genomics", "catalog", "imaging")
# Columns whose distinct values are listed in the planner prompt (if few enough).
PROFILE_SKIP = (
    "_source_value",
    "description",
    "study_name",
    "target_condition",
    "folder",
    "details",
    "note",
    "message",
    "file_name",
    "relative_path",
    "concept_name",
    "concept_code",
    "concept_synonym_name",
    "age_basis",
)


@dataclass
class ExecResult:
    sql: str
    columns: list[str] = field(default_factory=list)
    dtypes: list[str] = field(default_factory=list)
    df: pd.DataFrame | None = None
    row_count: int = 0  # total rows the query produces
    returned_rows: int = 0  # rows fetched for display
    truncated: bool = False
    elapsed_ms: float = 0.0
    error: str | None = None


class Warehouse:
    def __init__(self, path: Path = config.DB_PATH):
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} not found - build it with the PoC ingest and set IMODAR_WAREHOUSE")
        # Defence in depth (the SQL guard is the first line):
        #  * read-only file handle            -> no writes possible
        #  * external access disabled         -> no read_csv/read_parquet/httpfs/ATTACH of other files
        #  * no extension auto-install/load   -> no new capabilities at runtime
        #  * configuration locked             -> the above cannot be SET back by a query
        self.con = duckdb.connect(
            str(path),
            read_only=True,
            config={
                "enable_external_access": False,
                "autoinstall_known_extensions": False,
                "autoload_known_extensions": False,
            },
        )
        self.con.execute("SET lock_configuration = true")
        self.path = Path(path)
        self.schema = self._load_schema()

    # ---------------------------------------------------------------- introspection
    def _load_schema(self) -> dict[str, dict[str, dict[str, str]]]:
        rows = self.con.execute(
            "SELECT schema_name, table_name, column_name, data_type FROM duckdb_columns() "
            "WHERE schema_name IN ? ORDER BY schema_name, table_name, column_index",
            [list(QUERYABLE_SCHEMAS)],
        ).fetchall()
        out: dict[str, dict[str, dict[str, str]]] = {}
        for s, t, c, ty in rows:
            out.setdefault(s, {}).setdefault(t, {})[c] = ty
        return out

    def tables(self) -> list[str]:
        return [f"{s}.{t}" for s, ts in self.schema.items() for t in ts]

    def value_profile(self, max_distinct: int = 25) -> dict[str, list]:
        """Distinct values of low-cardinality text columns (helps the planner write exact filters)."""
        prof: dict[str, list] = {}
        cur = self.con.cursor()
        for s, ts in self.schema.items():
            for t, cols in ts.items():
                for c, ty in cols.items():
                    if ty != "VARCHAR" or any(k in c for k in PROFILE_SKIP) or c.endswith("_id"):
                        continue
                    n = cur.execute(f'SELECT count(DISTINCT "{c}") FROM {s}.{t}').fetchone()[0]
                    if 0 < n <= max_distinct:
                        vals = [
                            r[0]
                            for r in cur.execute(
                                f'SELECT DISTINCT "{c}" FROM {s}.{t} WHERE "{c}" IS NOT NULL ORDER BY 1'
                            ).fetchall()
                        ]
                        prof[f"{s}.{t}.{c}"] = vals
        return prof

    def query_df(self, sql: str, params: list | None = None) -> pd.DataFrame:
        """Internal trusted queries (not LLM generated)."""
        return self.con.cursor().execute(sql, params or []).df()

    # ---------------------------------------------------------------- execution of validated SQL
    def execute(
        self, sql: str, max_rows: int = config.MAX_RESULT_ROWS, timeout_s: float = config.QUERY_TIMEOUT_S
    ) -> ExecResult:
        res = ExecResult(sql=sql)
        cur = self.con.cursor()
        timer = threading.Timer(timeout_s, cur.interrupt)
        t0 = time.perf_counter()
        timer.start()
        try:
            cur.execute(sql)
            res.columns = [d[0] for d in cur.description]
            res.dtypes = [str(d[1]) for d in cur.description]
            rows = cur.fetchmany(max_rows + 1)
            res.truncated = len(rows) > max_rows
            rows = rows[:max_rows]
            res.df = pd.DataFrame(rows, columns=res.columns)
            res.returned_rows = len(rows)
            res.row_count = len(rows)
            if res.truncated:  # exact total, computed separately (logged as such)
                res.row_count = cur.execute(f"SELECT count(*) FROM ({sql.rstrip(';')})").fetchone()[0]
        except duckdb.InterruptException:
            res.error = f"Query exceeded timeout of {timeout_s:.0f}s and was cancelled."
        except duckdb.Error as e:
            res.error = f"{type(e).__name__}: {e}"
        finally:
            timer.cancel()
            res.elapsed_ms = (time.perf_counter() - t0) * 1000
        return res
