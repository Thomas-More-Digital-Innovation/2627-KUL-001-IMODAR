"""SQL guardrail: parse the LLM's SQL into an AST and reject anything that is not a
single, read-only SELECT over whitelisted tables/columns using known concept IDs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError, ParseError
from sqlglot.optimizer.qualify import qualify

DIALECT = "duckdb"

# Statement / clause node types that must never appear anywhere in the tree.
_FORBIDDEN_NODES = tuple(
    t
    for t in (
        getattr(exp, n, None)
        for n in (
            "Insert",
            "Update",
            "Delete",
            "Merge",
            "Create",
            "Drop",
            "Alter",
            "AlterTable",
            "TruncateTable",
            "Command",
            "Copy",
            "Pragma",
            "Set",
            "Use",
            "Attach",
            "Detach",
            "Install",
            "Load",
            "Grant",
            "Transaction",
            "Commit",
            "Rollback",
            "Into",
            "LoadData",
            "Export",
        )
    )
    if t is not None
)

# Function names that touch files, network, environment or engine internals.
_FORBIDDEN_FUNC = re.compile(
    r"^(read_\w*|parquet_\w*|glob|query|query_table|getenv|current_setting|duckdb_\w*|pragma_\w*|sniff_csv|"
    r"iceberg_\w*|delta_\w*|sqlite_\w*|postgres_\w*|mysql_\w*|http\w*|s3\w*|write_\w*|copy\w*|load_\w*|"
    r"install\w*|export\w*|import\w*|system|shell|setseed|nextval|currval)$",
    re.IGNORECASE,
)


@dataclass
class GuardReport:
    ok: bool
    sql: str  # normalised SQL that will be executed
    errors: list[str] = field(default_factory=list)
    checks: list[tuple[str, bool, str]] = field(default_factory=list)  # (check, passed, detail)
    tables: list[str] = field(default_factory=list)
    concept_ids: list[int] = field(default_factory=list)

    def fail(self, check: str, detail: str) -> GuardReport:
        self.ok = False
        self.errors.append(f"{check}: {detail}")
        self.checks.append((check, False, detail))
        return self

    def passed(self, check: str, detail: str = "") -> None:
        self.checks.append((check, True, detail))


def _func_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.name)
    try:
        return node.sql_name()
    except Exception:  # noqa: BLE001
        return type(node).__name__


def validate(sql: str, schema: dict[str, dict[str, dict[str, str]]], known_concepts: set[int]) -> GuardReport:
    rep = GuardReport(ok=True, sql=sql.strip().rstrip(";").strip())
    if not rep.sql:
        return rep.fail("non-empty", "empty query")

    # 1. parse: exactly one statement
    try:
        stmts = [s for s in sqlglot.parse(rep.sql, read=DIALECT) if s is not None]
    except ParseError as e:
        return rep.fail("syntax", str(e).splitlines()[0])
    if len(stmts) != 1:
        return rep.fail("single statement", f"{len(stmts)} statements found")
    tree = stmts[0]
    rep.passed("syntax", "parsed with sqlglot (duckdb dialect)")

    # 2. read-only: root must be a query, no forbidden nodes anywhere
    if not isinstance(tree, exp.Query):
        return rep.fail("read-only", f"root statement is {type(tree).__name__}, only SELECT allowed")
    bad = [type(n).__name__ for n in tree.walk() if isinstance(n, _FORBIDDEN_NODES)]
    if bad:
        return rep.fail("read-only", f"forbidden constructs: {sorted(set(bad))}")
    rep.passed("read-only", "single SELECT/WITH query")

    # 3. functions
    bad_f = sorted({_func_name(f) for f in tree.find_all(exp.Func) if _FORBIDDEN_FUNC.match(_func_name(f) or "")})
    if bad_f:
        return rep.fail("functions", f"forbidden functions: {bad_f}")
    rep.passed("functions", "no file/network/system functions")

    # 4. tables: every physical table must be whitelisted (CTE names excluded)
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    allowed = {(s.lower(), t.lower()) for s, ts in schema.items() for t in ts}
    by_name: dict[str, list[str]] = {}
    for s, t in allowed:
        by_name.setdefault(t, []).append(s)
    used = set()
    for t in tree.find_all(exp.Table):
        if not isinstance(t.this, exp.Identifier):  # table function in FROM (e.g. range(), read_csv())
            return rep.fail("tables", f"table-valued function not allowed: {t.sql(dialect=DIALECT)}")
        name, db = t.name.lower(), (t.db or "").lower()
        if t.catalog:
            return rep.fail("tables", f"catalog-qualified names not allowed: {t.sql(dialect=DIALECT)}")
        if not db and name in cte_names:
            continue
        if not db:  # tolerate unqualified names when unambiguous, and qualify them
            if len(by_name.get(name, [])) == 1:
                db = by_name[name][0]
                t.set("db", exp.to_identifier(db))
            else:
                return rep.fail("tables", f"unknown or ambiguous table '{name}'")
        if (db, name) not in allowed:
            return rep.fail("tables", f"table '{db}.{name}' is not whitelisted")
        used.add(f"{db}.{name}")
    rep.tables = sorted(used)
    rep.passed("tables", ", ".join(rep.tables) or "(none)")

    # 5. columns: let sqlglot's qualifier resolve every column against the real schema
    try:
        qualify(
            tree.copy(),
            schema=schema,
            dialect=DIALECT,
            validate_qualify_columns=True,
            quote_identifiers=False,
            identify=False,
        )
        rep.passed("columns", "all column references resolve against the warehouse schema")
    except OptimizeError as e:
        return rep.fail("columns", str(e))
    except Exception as e:  # noqa: BLE001 - qualifier can choke on exotic syntax; be strict
        return rep.fail("columns", f"could not verify column references ({type(e).__name__}: {e})")

    # 6. concept IDs: any literal that looks like a concept id must exist (no invented ids)
    lits = set()
    for lit in tree.find_all(exp.Literal):
        if not lit.is_string and re.fullmatch(r"\d+", lit.this or ""):
            v = int(lit.this)
            if v >= 2_000_000_000 or v in (8507, 8532):
                lits.add(v)
    unknown = sorted(lits - known_concepts)
    if unknown:
        return rep.fail("concept ids", f"concept_id(s) {unknown} do not exist in omop.concept")
    rep.concept_ids = sorted(lits)
    rep.passed("concept ids", f"{len(lits)} literal concept id(s), all exist" if lits else "none used")

    rep.sql = tree.sql(dialect=DIALECT, pretty=True)
    return rep
