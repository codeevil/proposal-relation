import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path

import sqlglot
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PGHOST = "localhost"
PGPORT = 9432
PGUSER = "postgres"
PGDATABASE = "dsb_10"
PSQL_BIN = "/home/liujianzhong/postgresql-15.5/bin/psql"

DATA_DIR = Path("./data")
PROPOSAL_PG_SCRIPT = Path(__file__).resolve().parent / "proposal_pg.py"
PROPOSAL_ONE_PG_SCRIPT = Path(__file__).resolve().parent / "proposal_one_pg.py"
PROPOSAL_RANK_PG_SCRIPT = Path(__file__).resolve().parent / "proposal_rank_pg.py"
PROPOSAL_COUNT = 20

# Database name → data/ subdirectory name. explain/stat/proposal artifacts are
# stored under ``data/{kind}/{db_dir}/``.
DB_TO_DIR = {
    "tpch": "tpch",
    "dsb_10": "tpcds",
    "imdb": "imdb",
}


def db_dir_for(database: str) -> str:
    return DB_TO_DIR.get(database, database)


def explain_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "explain" / db_dir_for(database) / f"{sql_path.stem}_explain.txt"


def stat_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "stat" / db_dir_for(database) / f"{sql_path.stem}_stat.json"


def proposal_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "proposal" / db_dir_for(database) / f"{sql_path.stem}_proposals.json"


def obo_proposal_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "obo_proposal" / db_dir_for(database) / f"{sql_path.stem}_proposals.json"


def rank_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "proposal" / db_dir_for(database) / f"{sql_path.stem}_rank.json"


def rank_obo_default_path(sql_path: Path, database: str) -> Path:
    return DATA_DIR / "obo_proposal" / db_dir_for(database) / f"{sql_path.stem}_rank.json"


def output_dir_for(database: str) -> Path:
    return DATA_DIR / "output" / db_dir_for(database)


@dataclass
class DbOptions:
    host: str = PGHOST
    port: int = PGPORT
    user: str = PGUSER
    database: str = PGDATABASE
    sleep: float = 3.0


def run_psql(sql: str, db: str = PGDATABASE, host: str = PGHOST,
             port: int = PGPORT, user: str = PGUSER, raise_on_error: bool = False):
    result = subprocess.run(
        [PSQL_BIN, "-h", host, "-p", str(port), "-U", user, "-d", db,
         "-X", "-A", "-t", "-q", "--no-psqlrc", "-v", "ON_ERROR_STOP=1"],
        input=sql,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        msg = f"psql failed: {result.stderr.strip()}"
        if raise_on_error:
            raise RuntimeError(msg)
        print(f"[ERROR] {msg}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


class PgMetadataCollector:
    def __init__(self, host: str = PGHOST, port: int = PGPORT,
                 user: str = PGUSER, dbname: str = PGDATABASE):
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "dbname": dbname,
        }
        self.conn = None
        self.default_schema = "public"
        self.result = {
            "sql_info": {
                "original_sql": "",
                "schema": "public",
                "extracted_tables": [],
            },
            "tables": {},
        }

    def parse_sql(self, sql_text: str):
        logger.info("Parsing SQL with sqlglot...")
        try:
            ast = sqlglot.parse_one(sql_text)
        except Exception as e:
            raise RuntimeError(f"SQL parse failed: {e}")

        self.result["sql_info"]["original_sql"] = ""

        # Extract all CTE aliases to skip when collecting base tables
        cte_aliases = set()
        for cte in ast.find_all(sqlglot.exp.CTE):
            if cte.alias:
                cte_aliases.add(cte.alias)

        # Extract base tables (not CTEs, not subquery aliases)
        table_info = {}
        alias_to_table = {}
        for node in ast.find_all(sqlglot.exp.Table):
            tbl_name = node.name
            tbl_schema = node.db or ""
            tbl_alias = node.alias or ""
            # Skip CTE references and subquery aliases
            if tbl_alias in cte_aliases:
                continue
            if tbl_name in cte_aliases:
                continue
            key = f"{tbl_schema}.{tbl_name}" if tbl_schema else tbl_name
            if key not in table_info:
                table_info[key] = (tbl_name, tbl_schema, tbl_alias)
            if tbl_alias:
                alias_to_table[tbl_alias] = key

        # Extract all column references
        col_nodes = list(ast.find_all(sqlglot.exp.Column))
        all_col_names = set()
        qualified_cols = {}
        unqualified_cols = set()
        for col_node in col_nodes:
            col_name = col_node.name
            all_col_names.add(col_name)
            tbl_ref = col_node.table
            if tbl_ref:
                tbl_ref = str(tbl_ref)
                tbl_key = alias_to_table.get(tbl_ref, tbl_ref)
                if tbl_key not in qualified_cols:
                    qualified_cols[tbl_key] = set()
                qualified_cols[tbl_key].add(col_name)
            else:
                unqualified_cols.add(col_name)

        # Resolve unqualified columns by querying the database
        if unqualified_cols and self.conn:
            logger.info("Resolving unqualified columns against database...")
            tbl_names = [info[0] for info in table_info.values()]
            tbl_schemas = [info[1] for info in table_info.values()]
            col_map = self._resolve_columns_to_tables(tbl_names, tbl_schemas, list(unqualified_cols))
            for col_name, tbl_key in col_map.items():
                if tbl_key not in qualified_cols:
                    qualified_cols[tbl_key] = set()
                qualified_cols[tbl_key].add(col_name)

        # Build extracted_tables list
        extracted_tables = []
        for tbl_name, tbl_schema, tbl_alias in table_info.values():
            schema_name = tbl_schema if tbl_schema else self.default_schema
            full_name = f"{schema_name}.{tbl_name}"
            extracted_tables.append({
                "table_name": tbl_name,
                "schema_name": schema_name,
                "alias": tbl_alias if tbl_alias else None,
            })

        # Build extracted_columns
        extracted_columns = {}
        for tbl_key, cols in qualified_cols.items():
            if "." in tbl_key:
                extracted_columns[tbl_key] = sorted(cols)
            else:
                extracted_columns[f"{self.default_schema}.{tbl_key}"] = sorted(cols)

        self.result["sql_info"]["extracted_tables"] = extracted_tables
        return extracted_tables, extracted_columns

    def _resolve_columns_to_tables(self, tbl_names, tbl_schemas, col_names):
        if not col_names or not tbl_names:
            return {}
        schema_conditions = " OR ".join(
            f"(n.nspname = {schema!r} AND c.relname = {table!r})"
            for table, schema in zip(tbl_names, tbl_schemas)
            if schema
        )
        unqualified_conditions = " OR ".join(
            f"c.relname = {table!r}" for table in tbl_names
        )
        # Build a single query to find column -> table mapping
        params = tuple(col_names)
        placeholders = ", ".join("%s" for _ in col_names)
        # First try with schema-qualified tables
        if schema_conditions:
            query = f"""
                SELECT DISTINCT a.attname, n.nspname, c.relname
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE ({schema_conditions})
                  AND a.attname IN ({placeholders})
                  AND a.attnum > 0
                  AND NOT a.attisdropped
            """
        else:
            query = f"""
                SELECT DISTINCT a.attname, n.nspname, c.relname
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE ({unqualified_conditions})
                  AND a.attname IN ({placeholders})
                  AND a.attnum > 0
                  AND NOT a.attisdropped
            """
        with self.conn.cursor() as cur:
            cur.execute(query, tuple(col_names))
            rows = cur.fetchall()
        result = {}
        for col_name, nspname, relname in rows:
            full_name = f"{nspname}.{relname}"
            if col_name not in result:
                result[col_name] = full_name
        return result

    def connect_db(self):
        logger.info("Connecting to PostgreSQL...")
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = True
            with self.conn.cursor() as cur:
                cur.execute("SELECT current_schema;")
                self.default_schema = cur.fetchone()[0]
            self.result["sql_info"]["schema"] = self.default_schema
            logger.info(f"Connected, default schema: {self.default_schema}")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    def collect_table_metadata(self, schema: str, table: str) -> dict:
        query = """
            SELECT c.relname,
                   n.nspname AS relnamespace,
                   c.reltuples::bigint,
                   c.relpages,
                   c.relallvisible
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s AND c.relname = %s
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (schema, table))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "relname": row["relname"],
            "relnamespace": row["relnamespace"],
            "reltuples": row["reltuples"] if row["reltuples"] is not None else 0,
            "relpages": row["relpages"] if row["relpages"] is not None else 0,
            "relallvisible": row["relallvisible"] if row["relallvisible"] is not None else 0,
        }

    def collect_indexes(self, schema: str, table: str) -> list:
        query = """
            SELECT i.relname AS index_name,
                   am.amname AS index_type,
                   idx.indisunique,
                   idx.indisprimary,
                   idx.indpred IS NOT NULL AS is_partial,
                   array_agg(a.attname ORDER BY unnest_pos) AS index_columns
            FROM pg_index idx
            JOIN pg_class i ON idx.indexrelid = i.oid
            JOIN pg_class t ON idx.indrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            JOIN pg_am am ON i.relam = am.oid
            JOIN LATERAL unnest(idx.indkey) WITH ORDINALITY AS key(key_attnum, unnest_pos) ON TRUE
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = key.key_attnum
            WHERE n.nspname = %s AND t.relname = %s
              AND a.attnum > 0 AND NOT a.attisdropped
            GROUP BY i.relname, idx.indexrelid, am.amname, idx.indisunique, idx.indisprimary, idx.indpred
            ORDER BY i.relname
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (schema, table))
            rows = cur.fetchall()
        return [
            {
                "index_name": r["index_name"],
                "index_type": r["index_type"],
                "index_columns": r["index_columns"],
                "is_unique": r["indisunique"],
                "is_primary": r["indisprimary"],
                "is_partial": r["is_partial"],
            }
            for r in rows
        ]

    def collect_column_statistics(self, schema: str, table: str, columns: list = None) -> dict:
        if columns is None:
            return {}
        # pg_stats returns one row per column, we filter by the columns we need
        col_names = [c for c in columns if c is not None]
        if not col_names:
            return {}
        result = {}
        for col in col_names:
            query = """
                SELECT attname, n_distinct, null_frac
                FROM pg_stats
                WHERE schemaname = %s AND tablename = %s AND attname = %s
            """
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (schema, table, col))
                row = cur.fetchone()
            if not row:
                result[col] = None
                continue
            result[col] = {
                "attname": row["attname"],
                "n_distinct": row["n_distinct"] if row["n_distinct"] is not None else None,
                "null_frac": row["null_frac"] if row["null_frac"] is not None else None,
            }
        return result

    @staticmethod
    def _parse_pg_array(text: str) -> list:
        if text is None:
            return None
        # pg_stats returns arrays in PostgreSQL format like {v1,v2,v3}
        text = text.strip()
        if not text.startswith("{"):
            # Try JSON parse for numeric arrays that pg outputs as JSON
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return None
        # PostgreSQL array format: {val1,val2,val3}
        inner = text[1:-1]
        if not inner:
            return []
        parts = []
        buf = []
        in_quotes = False
        for ch in inner:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == "," and not in_quotes:
                parts.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        if buf:
            parts.append("".join(buf))
        result = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # Try numeric first
            try:
                if "." in p:
                    result.append(float(p))
                else:
                    result.append(int(p))
            except (ValueError, TypeError):
                result.append(p)
        return result

    def collect_all(self, sql_text: str):
        logger.info("Starting metadata collection...")
        self.connect_db()
        extracted_tables, extracted_columns = self.parse_sql(sql_text)

        for tbl in extracted_tables:
            schema = tbl["schema_name"]
            table = tbl["table_name"]
            full_name = f"{schema}.{table}"
            logger.info(f"Collecting metadata for {full_name}...")

            # Check if table exists
            check_query = "SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname = %s AND c.relname = %s AND c.relkind = 'r'"
            with self.conn.cursor() as cur:
                cur.execute(check_query, (schema, table))
                if not cur.fetchone():
                    logger.warning(f"Table {full_name} not found or is not a base table, skipping")
                    continue

            table_meta = self.collect_table_metadata(schema, table)
            indexes = self.collect_indexes(schema, table)

            # Collect column statistics only for columns involved in the SQL
            sql_columns = extracted_columns.get(full_name, [])
            # Also check if column appears in the table's default schema
            if not sql_columns and schema == "public":
                sql_columns = extracted_columns.get(table, [])
            col_stats = self.collect_column_statistics(schema, table, sql_columns) if sql_columns else {}

            self.result["tables"][full_name] = {
                "table_metadata": table_meta,
                "indexes": indexes,
                "column_statistics": col_stats,
            }

        logger.info("Metadata collection completed.")

    def export_json(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.result, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON output written to: {path}")


def gen_explain(sql_path: Path, opts: DbOptions, output_path: Path = None) -> Path:
    """Run EXPLAIN ANALYZE for a SQL file and write the output to disk.

    Returns the resolved output path. The caller is expected to have already
    validated the SQL file's existence and non-empty content.
    """
    sql_content = sql_path.read_text(encoding="utf-8").strip()
    explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}", db=opts.database,
                              host=opts.host, port=opts.port, user=opts.user)

    output_path = Path(output_path) if output_path else explain_default_path(sql_path, opts.database)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(explain_output, encoding="utf-8")
    logger.info(f"EXPLAIN ANALYZE written to: {output_path}")
    return output_path


def cmd_gen_explain(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)
    if not sql_path.read_text(encoding="utf-8").strip():
        print(f"[ERROR] SQL file is empty: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user, database=args.database)
    output_path = Path(args.output) if args.output else None
    written = gen_explain(sql_path, opts, output_path=output_path)
    print(f"[INFO] EXPLAIN ANALYZE written to: {written}")


def _run_psql_with_capture(sql: str, opts: DbOptions):
    """Run psql and return (returncode, stdout, stderr). Does not exit on error."""
    try:
        result = subprocess.run(
            [PSQL_BIN, "-h", opts.host, "-p", str(opts.port), "-U", opts.user, "-d", opts.database,
             "-X", "-A", "-t", "-q", "--no-psqlrc", "-v", "ON_ERROR_STOP=1"],
            input=sql,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
    except subprocess.TimeoutExpired as e:
        def _to_str(b):
            return b.decode("utf-8", errors="replace") if isinstance(b, bytes) else (b or "")
        extra = _to_str(e.stderr).strip()
        msg = "query execution exceeded 60s timeout (killed)"
        if extra:
            msg = f"{msg}: {extra}"
        return -1, _to_str(e.stdout), msg
    return result.returncode, result.stdout, result.stderr


def _format_hint_error_message(stderr_text: str) -> str:
    """Re-order pg_hint_plan's stderr output for hint syntax errors.

    pg_hint_plan emits a hint error as a sequence of:
      INFO:  pg_hint_plan: hint syntax error ...
      DETAIL:  ...
      ... (possibly more INFO/DETAIL blocks)
      NOTICE:  pg_hint_plan:
      used hint:
      not used hint:
      duplication hint:
      error hint:
      <one or more lines of the offending hint text>

    Re-organized as:
      1. The "error hint:" body (joined with spaces)         - dropped if empty
      2. All DETAIL: lines, in order
      3. The 2nd, 3rd, ... INFO: lines (i.e. INFO blocks[1:])
      4. The 1st INFO: line (i.e. INFO blocks[0])
    Lines are joined with single spaces inside each section.
    """
    lines = (stderr_text or "").splitlines()

    info_lines = []   # the actual text after each "INFO:" prefix, in order
    detail_lines = [] # the actual text after each "DETAIL:" prefix, in order
    error_hint_body_lines = []  # lines after "error hint:" until next banner / EOF

    i = 0
    in_notice = False
    seen_error_hint_header = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("INFO:") and "pg_hint_plan" in stripped and "hint syntax error" in stripped.lower():
            info_lines.append(stripped[len("INFO:"):].strip())
            i += 1
            continue
        if stripped.startswith("DETAIL:"):
            detail_lines.append(stripped[len("DETAIL:"):].strip())
            i += 1
            continue
        if stripped.startswith("NOTICE:") and "pg_hint_plan" in stripped:
            in_notice = True
            i += 1
            continue
        if in_notice:
            if stripped == "error hint:":
                seen_error_hint_header = True
                i += 1
                continue
            if seen_error_hint_header:
                # Subsequent lines belong to the offending hint text until the
                # notice block ends (blank line / next banner / EOF).
                if stripped == "":
                    i += 1
                    continue
                error_hint_body_lines.append(stripped)
                i += 1
                continue
        i += 1

    parts = []
    if error_hint_body_lines:
        parts.append(" ".join(error_hint_body_lines))
    if detail_lines:
        parts.append(" ".join(detail_lines))
    if len(info_lines) > 1:
        parts.append(" ".join(info_lines[1:]))
    if info_lines:
        parts.append(info_lines[0])
    return " | ".join(parts)


def _find_balanced_paren(text: str, open_idx: int) -> int:
    """Given the index of an '(' in ``text``, return the index of its matching ')'.

    Returns -1 if no balanced closing paren is found. Ignores parens that appear
    inside single- or double-quoted regions.
    """
    depth = 0
    i = open_idx
    in_single = False
    in_double = False
    while i < len(text):
        ch = text[i]
        if in_single:
            if ch == "'":
                in_single = False
        elif in_double:
            if ch == '"':
                in_double = False
        else:
            if ch == "'":
                in_single = True
            elif ch == '"':
                in_double = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def _split_top_level(body: str, sep: str = " ") -> list:
    """Split ``body`` by ``sep`` only at parenthesis depth 0 (quote-aware)."""
    parts = []
    buf = []
    depth = 0
    in_single = False
    in_double = False
    i = 0
    while i < len(body):
        ch = body[i]
        if in_single:
            buf.append(ch)
            if ch == "'":
                in_single = False
        elif in_double:
            buf.append(ch)
            if ch == '"':
                in_double = False
        else:
            if ch == "'":
                in_single = True
                buf.append(ch)
            elif ch == '"':
                in_double = True
                buf.append(ch)
            elif ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                buf.append(ch)
            elif depth == 0 and body.startswith(sep, i):
                parts.append("".join(buf))
                buf = []
                i += len(sep)
                continue
            else:
                buf.append(ch)
        i += 1
    if buf:
        parts.append("".join(buf))
    return parts


def _is_balanced(body: str) -> bool:
    """Return True if ``body`` has balanced parens (quote-aware)."""
    depth = 0
    in_single = False
    in_double = False
    for ch in body:
        if in_single:
            if ch == "'":
                in_single = False
        elif in_double:
            if ch == '"':
                in_double = False
        else:
            if ch == "'":
                in_single = True
            elif ch == '"':
                in_double = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    return False
    return depth == 0 and not in_single and not in_double


def _extract_leading_blocks(hint: str) -> list:
    """Find all ``Leading(...)`` blocks in ``hint`` and return their (start, end, body).

    ``start`` and ``end`` are the indices of the '(' and ')' that bound the
    ``Leading`` argument list. ``body`` is the inner text between them.

    Robust to nested parens inside the argument list (e.g. nested Leading forms
    or bushy-tree groupings).
    """
    blocks = []
    pattern = re.compile(r"Leading\s*\(", re.IGNORECASE)
    for m in pattern.finditer(hint):
        open_idx = m.end() - 1  # index of '('
        close_idx = _find_balanced_paren(hint, open_idx)
        if close_idx == -1:
            continue
        body = hint[open_idx + 1:close_idx]
        blocks.append((open_idx, close_idx, body))
    return blocks


def _classify_leading(body: str) -> str:
    """Classify a ``Leading`` body as ``"left_deep"``, ``"nested"``, or ``"invalid"``.

    - ``left_deep``: a flat list of >=3 bare table identifiers, possibly wrapped
      in zero or more redundant outer paren pairs. E.g. ``a b c``,
      ``(a b c)``, ``((a b c))``.
    - ``nested``: a bushy tree of >=2 sibling parenthesised subtrees, either
      with the required outer wrap ``((a b) (c d))`` or without it
      ``(a b) (c d)``.
    - ``invalid``: mixed tokens, unbalanced parens, <3 tables for left-deep,
      or any shape this classifier does not recognise (pass through unchanged
      and let pg_hint_plan surface a hint_error).
    """
    body = body.strip()
    if not body:
        return "invalid"
    if not _is_balanced(body):
        return "invalid"

    top_level = [t.strip() for t in _split_top_level(body, " ") if t.strip()]
    if not top_level:
        return "invalid"

    def _is_group(tok: str) -> bool:
        t = tok.strip()
        return t.startswith("(") and t.endswith(")") and _is_balanced(t[1:-1])

    def _is_bare(tok: str) -> bool:
        t = tok.strip()
        return bool(t) and "(" not in t and ")" not in t

    # All bare identifiers at top level -> left-deep core (no redundant parens).
    if all(_is_bare(t) for t in top_level):
        return "left_deep" if len(top_level) >= 3 else "invalid"

    # >=2 sibling parenthesised groups at top level -> nested WITHOUT outer wrap.
    if len(top_level) >= 2 and all(_is_group(t) for t in top_level):
        return "nested"

    # Single parenthesised group at top level -> inspect its content to
    # distinguish left-deep-with-redundant-parens from nested-with-outer-wrap.
    if len(top_level) == 1 and _is_group(top_level[0]):
        inner = top_level[0][1:-1].strip()
        inner_top = [t.strip() for t in _split_top_level(inner, " ") if t.strip()]
        # Inner is all bare -> left-deep with redundant outer parens.
        if inner_top and all(_is_bare(t) for t in inner_top):
            return "left_deep" if len(inner_top) >= 3 else "invalid"
        # Inner is multiple sibling groups -> nested with outer wrap (correct).
        if len(inner_top) >= 2 and all(_is_group(t) for t in inner_top):
            return "nested"
        # Inner is itself a single group -> deeper nesting; recurse to classify
        # the inner content (handles ((a b c)), (((a b) (c d))), etc.).
        if len(inner_top) == 1 and _is_group(inner_top[0]):
            return _classify_leading(inner)
        return "invalid"

    return "invalid"


def _normalize_left_deep_leading(body: str) -> str:
    """Strip redundant outer paren pairs from a left-deep ``Leading`` body.

    A left-deep tree (>=3 tables) must have NO extra paren pairs in the body;
    the only parens around the table list are ``Leading(...)``'s own. E.g.
    ``((a b c))`` -> ``a b c``, ``(a b c)`` -> ``a b c``, ``a b c`` -> ``a b c``.

    Only called on bodies already classified as ``left_deep``; safe no-op for
    a bare core. Peeling stops as soon as the outer paren no longer wraps the
    whole body (so it never touches a genuinely nested structure).
    """
    stripped = body.strip()
    while stripped.startswith("(") and stripped.endswith(")"):
        # Ensure the leading '(' actually matches the very last ')': if the
        # match lands earlier, the outer parens don't wrap the whole body and
        # peeling would corrupt a nested subtree.
        match_idx = _find_balanced_paren(stripped, 0)
        if match_idx != len(stripped) - 1:
            break
        inner = stripped[1:-1].strip()
        if not _is_balanced(inner):
            break
        stripped = inner
    return stripped


def _normalize_nested_leading(body: str) -> str:
    """Ensure a nested Leading body has its required outer paren wrap.

    pg_hint_plan requires nested Leading forms to be wrapped in an extra pair
    of parens, e.g. ``Leading( ((t1 t2) (t3 t4)) )``. Bare groupings such as
    ``((t1 t2) (t3 t4))`` (matched parens, no outer wrap) are rejected because
    the top level contains two sibling groups rather than one wrapped tree.

    This function detects that case and inserts the outer wrap. If internal
    subtrees are themselves invalid (mixed tokens, unbalanced parens), they are
    left untouched — the caller should surface a hint_error via the normal
    ``pg_hint_plan`` error path rather than silently corrupting the input.
    """
    stripped = body.strip()
    if not stripped:
        return body

    top_level = [t.strip() for t in _split_top_level(body, " ") if t.strip()]

    def _is_group(tok: str) -> bool:
        t = tok.strip()
        return t.startswith("(") and t.endswith(")") and _is_balanced(t[1:-1])

    # The required outer wrap exists iff, after stripping, the body has exactly
    # one whitespace-separated top-level token that itself is a parenthesised
    # balanced group. Two-or-more top-level groups (e.g. "(ta tb) (tc td)")
    # mean the outer wrap is missing.
    has_outer_wrap = (
        len(top_level) == 1 and _is_group(top_level[0])
    )

    if has_outer_wrap:
        # Preserve the body's original whitespace verbatim when no rewrite is
        # needed; only strip() if we actually need to insert the outer wrap.
        return body

    if len(top_level) >= 2 and all(_is_group(t) for t in top_level):
        return f"({stripped})"
    return body


def _fix_leading_hint(hint: str) -> str:
    """Walk a hint string, normalise every ``Leading(...)`` block.

    Currently performs:
      - left_deep Leading: strips redundant outer paren pairs so the body is
        a flat list of bare identifiers (the ``Leading(a b c)`` form). Catches
        ``Leading((a b c))`` / ``Leading(((a b c)))`` and reduces them to
        ``Leading(a b c)``.
      - nested Leading: adds the required outer paren wrap if missing.

    Returns the (possibly rewritten) hint string. Designed to be extensible:
    add new Leading normalisations by extending the steps inside this function
    rather than touching callers.
    """
    blocks = _extract_leading_blocks(hint)
    if not blocks:
        return hint

    out = []
    cursor = 0
    for open_idx, close_idx, body in blocks:
        out.append(hint[cursor:open_idx + 1])  # up to and including '('
        kind = _classify_leading(body)
        if kind == "left_deep":
            new_body = _normalize_left_deep_leading(body)
        elif kind == "nested":
            new_body = _normalize_nested_leading(body)
        else:
            new_body = body
        out.append(new_body)
        out.append(")")
        cursor = close_idx + 1
    out.append(hint[cursor:])
    return "".join(out)


def run_one_proposal(proposal_id: int, label: str, hint: str, sql_content: str, opts: DbOptions):
    """Execute a single proposal (optional hint + SQL) and measure elapsed time in ms."""
    hint = _fix_leading_hint(hint) if hint else hint
    sql_to_run = f"{hint}\n{sql_content}" if hint else sql_content
    start = time.perf_counter()
    rc, _stdout, stderr = _run_psql_with_capture(sql_to_run, opts)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    if rc == 0:
        # pg_hint_plan emits hint syntax errors as INFO (not ERROR) and does not
        # change the exit code. Detect these and flag them separately.
        stderr_text = stderr or ""
        if "hint syntax error" in stderr_text.lower() and "pg_hint_plan" in stderr_text:
            status = "hint_error"
            error_msg = _format_hint_error_message(stderr_text)
            print(f"[HINT_ERROR] {label}: {error_msg}", file=sys.stderr)
        else:
            status = "ok"
            error_msg = ""
    elif rc == -1:
        status = "timeout"
        error_msg = stderr.strip() if stderr else "query execution exceeded 60s timeout (killed)"
        print(f"[TIMEOUT] {label}: {error_msg}", file=sys.stderr)
    else:
        stderr_clean = stderr.strip() if stderr else ""
        first_error = ""
        for line in stderr_clean.splitlines():
            if line.startswith("ERROR:"):
                first_error = line[len("ERROR:"):].strip()
                break
        is_hint_error = "hint syntax error" in stderr_clean.lower()
        status = "hint_error" if is_hint_error else "error"
        if is_hint_error:
            error_msg = _format_hint_error_message(stderr_clean)
        else:
            error_msg = first_error or (stderr_clean.splitlines()[0] if stderr_clean else f"psql exit {rc}")
        print(f"[{status.upper()}] {label}: {error_msg}", file=sys.stderr)

    return {
        "proposal_id": proposal_id,
        "label": label,
        "hint": hint,
        "elapsed_ms": elapsed_ms,
        "status": status,
        "error_msg": error_msg,
    }


def _print_results_table(results, header: str = None, output_file = None,
                         rank_best_id: int = None):
    baseline_ms = None
    for r in results:
        if r["label"] == "baseline" and r["status"] == "ok":
            baseline_ms = r["elapsed_ms"]

    headers = ["Proposal ID", "Label", "Elapsed (ms)", "Speedup", "AgentRankBest", "Status", "Error"]
    rows = []
    for r in results:
        if r["status"] == "ok":
            elapsed = f"{r['elapsed_ms']:.2f}"
            speedup = f"{baseline_ms / r['elapsed_ms']:.2f}x" if baseline_ms else "N/A"
            err = ""
        elif r["status"] == "hint_error":
            elapsed = f"{r['elapsed_ms']:.2f}"
            speedup = f"{baseline_ms / r['elapsed_ms']:.2f}x" if baseline_ms else "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        elif r["status"] == "timeout":
            elapsed = "timeout"
            speedup = "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        else:
            elapsed = "error"
            speedup = "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        rank_best = "Yes" if (rank_best_id is not None and r["proposal_id"] == rank_best_id) else ""
        rows.append([str(r["proposal_id"]), r["label"], elapsed, speedup, rank_best, r["status"], err])

    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)

    def _emit(line: str):
        print(line)
        if output_file is not None:
            output_file.write(line + "\n")

    _emit("")
    if header:
        _emit(f"=== {header} ===")
    _emit(fmt.format(*headers))
    _emit(sep)
    for row in rows:
        _emit(fmt.format(*row))
    _emit("")



def _generate_stat_table(results_per_query: list[dict], stat_path: Path) -> None:
    """Generate a summary statistics table from per-query benchmark results.

    For each query (identified by ``"sql_name"``), selects:
      - baseline row  (label == "baseline")
      - best proposal row (minimum elapsed_ms among rows with status "ok")

    Writes a formatted table to ``stat_path`` with columns:
      Query | Baseline(ms) | Best-Proposal | Best(ms) | Speedup-Base | AgentRankBest | Status | Error
    """
    stat_path = Path(stat_path)
    stat_path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["Query", "Baseline(ms)", "Best-Proposal",
               "Best(ms)", "Speedup-Base", "AgentRankBest", "Status", "Error"]
    rows = []

    for entry in results_per_query:
        sql_name = entry["sql_name"]
        results = entry["results"]
        rank_best_id = entry.get("rank_best_id")

        baseline_ms = None
        best_result = None
        best_ms = float("inf")

        for r in results:
            if r["label"] == "baseline" and r["status"] == "ok":
                baseline_ms = r["elapsed_ms"]
            if (r["label"] != "baseline"
                    and r["status"] in ("ok", "hint_error")
                    and r["elapsed_ms"] < best_ms):
                best_ms = r["elapsed_ms"]
                best_result = r

        if best_result is not None:
            best_label = best_result["label"]
            best_elapsed = f"{best_ms:.2f}"
            speedup_base = f"{baseline_ms / best_ms:.2f}x" if baseline_ms else "N/A"
            status = best_result["status"]
            error = best_result.get("error_msg", "")
            if len(error) > 40:
                error = error[:37] + "..."
        else:
            # No successful proposal found
            best_label = "N/A"
            best_elapsed = "N/A"
            speedup_base = "N/A"
            status = "no_success"
            error = ""

        bl_str = f"{baseline_ms:.2f}" if baseline_ms else "N/A"
        rank_best_str = str(rank_best_id) if rank_best_id is not None else "-"

        rows.append([sql_name, bl_str, best_label, best_elapsed,
                     speedup_base, rank_best_str, status, error])

    if not rows:
        logger.info("No query results to summarize.")
        return

    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)

    lines = []
    lines.append(fmt.format(*headers))
    lines.append(sep)
    for row in rows:
        lines.append(fmt.format(*row))

    text = "\n".join(lines) + "\n"
    stat_path.write_text(text, encoding="utf-8")
    logger.info(f"Stat summary written to: {stat_path}")


def _generate_lero_stat_table(results: list[dict], stat_path: Path) -> None:
    """Generate a summary table for the ``test-lero`` command.

    For each query (identified by ``"sql_name"``), records baseline time,
    lero time, Lero-vs-baseline speedup, Lero status and Lero error.

    Writes a formatted table to ``stat_path`` with columns:
      Query | Baseline(ms) | Lero(ms) | Speedup | Status | Error
    """
    stat_path = Path(stat_path)
    stat_path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["Query", "Baseline(ms)", "Lero(ms)", "Speedup", "Status", "Error"]
    rows = []

    for r in results:
        sql_name = r["sql_name"]
        baseline_ms = r.get("baseline_ms")
        lero_ms = r.get("lero_ms")
        status = r.get("lero_status", "")
        error = r.get("lero_error", "")
        if len(error) > 40:
            error = error[:37] + "..."

        bl_str = f"{baseline_ms:.2f}" if baseline_ms else "N/A"
        lero_str = f"{lero_ms:.2f}" if lero_ms else "N/A"
        speedup = f"{baseline_ms / lero_ms:.2f}x" if (baseline_ms and lero_ms) else "N/A"

        rows.append([sql_name, bl_str, lero_str, speedup, status, error])

    if not rows:
        logger.info("No query results to summarize.")
        return

    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)

    lines = [fmt.format(*headers), sep]
    for row in rows:
        lines.append(fmt.format(*row))

    text = "\n".join(lines) + "\n"
    stat_path.write_text(text, encoding="utf-8")
    logger.info(f"Lero stat summary written to: {stat_path}")


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()


def _escape_raw_control_chars_in_json_strings(text: str) -> str:
    """Escape raw \\n/\\r/\\t that appear inside JSON string values.

    The LLM often emits literal newlines (and tabs) inside string values instead of
    the JSON-escaped ``\\n`` / ``\\t``. Standard ``json.loads`` rejects these as
    'Invalid control character'. This pass walks the text and only escapes control
    characters while we are inside a JSON string (between unescaped double quotes).
    """
    out = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\":
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch == "\n":
            out.append("\\n")
        elif in_string and ch == "\r":
            out.append("\\r")
        elif in_string and ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def _parse_proposals_lenient(text: str):
    """Parse a JSON array of proposal objects, dropping malformed entries.

    The LLM occasionally emits objects with malformed JSON (e.g. missing closing
    quotes on a string). Standard ``json.loads`` fails on the whole array, which
    loses every good proposal. Instead, decode the top-level ``[``, then parse
    each entry with ``raw_decode`` and keep only the ones that succeed.

    Returns ``(proposals_list, dropped_count)``.
    """
    text = text.strip()
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n and text[idx] in " \t\r\n":
        idx += 1
    if idx >= n or text[idx] != "[":
        raise json.JSONDecodeError("Expected top-level JSON array", text, idx)
    idx += 1

    proposals = []
    dropped = 0
    while True:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            raise json.JSONDecodeError("Unterminated JSON array", text, idx)
        if text[idx] == "]":
            break
        if text[idx] != "{":
            raise json.JSONDecodeError("Expected object start", text, idx)
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as e:
            dropped += 1
            print(f"[WARN] Dropping malformed proposal at pos {idx}: {e.msg}", file=sys.stderr)
            # Skip to the next '},' (next element) or '}<ws>]' (end of array)
            # so we land on a clean object boundary. If we can't find one
            # within a reasonable window, abort the recovery to avoid an
            # infinite loop.
            # Note: literal '\n' inside JSON strings is rewritten to the
            # two-char sequence '\\n' (backslash + n) by the escape pass above.
            scan_end = min(n, idx + 5000)
            scan = text[idx:scan_end]
            ws = r"(?:\s|\\n|\\r|\\t)*"
            candidates = []
            for m in re.finditer(rf"\}},{ws}\{{", scan):
                candidates.append(idx + m.end() - 1)  # position of next '{'
            for m in re.finditer(rf"\}}{ws}\]", scan):
                candidates.append(idx + m.end() - 1)  # position of ']' -> array end
            if not candidates:
                raise json.JSONDecodeError(
                    "Could not recover from malformed proposal (no object boundary found)",
                    text, idx,
                ) from e
            idx = candidates[0]
            continue
        proposals.append(obj)
        idx = end
        # Skip whitespace and optional comma
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx < n and text[idx] == ",":
            idx += 1
    return proposals, dropped


def _load_rank_best_id(sql_path: Path, database: str, proposals_kind: str):
    """Read the agent_rank result (``{stem}_rank.json``) and return the chosen
    best proposal id, or None if missing/unparseable."""
    rank_path = DATA_DIR / proposals_kind / db_dir_for(database) / f"{Path(sql_path).stem}_rank.json"
    if not rank_path.exists():
        return None
    try:
        text = _escape_raw_control_chars_in_json_strings(
            _strip_markdown_fence(rank_path.read_text(encoding="utf-8")))
        data = json.loads(text)
        bid = data.get("best_proposal_id")
        if isinstance(bid, bool):
            return None
        if isinstance(bid, int):
            return bid
        if isinstance(bid, float) and bid.is_integer():
            return int(bid)
        return None
    except Exception:
        pass
    try:
        m = re.search(r'"best_proposal_id"\s*:\s*(\d+)', rank_path.read_text(encoding="utf-8"))
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def run_proposals(sql_path: Path, opts: DbOptions, proposals_path: Path = None,
                  output_path: Path = None, output_file = None, header: str = None,
                  proposals_kind: str = "proposal"):
    """Execute baseline + each proposal in the proposals file, print timing table. Returns results.

    ``proposals_kind`` selects the proposals source + rank file location and
    controls the default output filename suffix: ``"proposal"`` (default) reads
    ``data/proposal/{db_dir}/`` and ``"obo_proposal"`` reads ``data/obo_proposal/{db_dir}/``.

    The formatted table is written to ``output_path`` (default
    ``data/output/{db_dir}/run_proposals[_obo]_{stem}_result.txt``). Pass
    ``output_file`` for callers that already hold an open handle (e.g.
    ``run_proposals_all`` aggregating many tables into one file) — when supplied
    it overrides ``output_path``.
    """
    sql_content = sql_path.read_text(encoding="utf-8").strip()

    if proposals_path is None:
        proposals_path = (obo_proposal_default_path(sql_path, opts.database)
                          if proposals_kind == "obo_proposal"
                          else proposal_default_path(sql_path, opts.database))
    proposals_path = Path(proposals_path)
    if not proposals_path.exists():
        print(f"[ERROR] Proposals file not found: {proposals_path}", file=sys.stderr)
        sys.exit(1)
    proposals_text = _escape_raw_control_chars_in_json_strings(
        _strip_markdown_fence(proposals_path.read_text(encoding="utf-8")))
    proposals, _dropped = _parse_proposals_lenient(proposals_text)
    if not isinstance(proposals, list):
        print(f"[ERROR] Proposals file must be a JSON array", file=sys.stderr)
        sys.exit(1)

    rank_best_id = _load_rank_best_id(sql_path, opts.database, proposals_kind)
    tag = "_obo" if proposals_kind == "obo_proposal" else ""

    if header is None:
        header = sql_path.name

    if output_file is None:
        resolved_output_path = (Path(output_path) if output_path
                                else output_dir_for(opts.database) / f"run_proposals{tag}_{sql_path.stem}_result.txt")
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        own_file = open(resolved_output_path, "w", encoding="utf-8")
        logger.info(f"Summary output: {resolved_output_path}")
    else:
        own_file = None

    results = []

    try:
        logger.info("Warmup: baseline (no hint)...")
        run_one_proposal(-1, "baseline-warmup", "", sql_content, opts)
        time.sleep(opts.sleep)

        logger.info("Running baseline (no hint)...")
        results.append(run_one_proposal(0, "baseline", "", sql_content, opts))

        for p in proposals:
            pid = p.get("proposal_id")
            hint = p.get("hint_combination") or ""
            label = f"proposal_{pid}"
            logger.info(f"Running {label}...")
            results.append(run_one_proposal(pid, label, hint, sql_content, opts))
            time.sleep(opts.sleep)

        sink = output_file if output_file is not None else own_file
        _print_results_table(results, header=header, output_file=sink,
                             rank_best_id=rank_best_id)
    finally:
        if own_file is not None:
            own_file.close()
            print(f"[INFO] Summary written to: {resolved_output_path}")
    return results


def cmd_run_proposals(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_proposals(sql_path, opts, proposals_path=args.proposals,
                  output_path=args.output)


def gen_stat(sql_path: Path, opts: DbOptions, output_path: Path = None) -> Path:
    """Generate metadata & statistics JSON for a SQL file. Returns output path."""
    sql_content = sql_path.read_text(encoding="utf-8").strip()

    output_path = Path(output_path) if output_path else stat_default_path(sql_path, opts.database)

    collector = PgMetadataCollector(
        host=opts.host, port=opts.port, user=opts.user, dbname=opts.database,
    )
    try:
        collector.collect_all(sql_content)
        collector.export_json(str(output_path))
    finally:
        collector.close()
    return output_path


def cmd_gen_stat(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database)
    gen_stat(sql_path, opts, output_path=args.output)


def gen_proposals(sql_path: Path, opts: DbOptions, stat_path: Path = None,
                  explain_path: Path = None, output_path: Path = None) -> Path:
    """Invoke proposal_pg.py to generate the proposals JSON file. Returns output path."""
    stat_path = Path(stat_path) if stat_path else stat_default_path(sql_path, opts.database)
    explain_path = Path(explain_path) if explain_path else explain_default_path(sql_path, opts.database)
    output_path = Path(output_path) if output_path else proposal_default_path(sql_path, opts.database)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(PROPOSAL_PG_SCRIPT),
        "--sql", str(sql_path),
        "--stat", str(stat_path),
        "--explain", str(explain_path),
        "--output", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"[ERROR] proposal_pg failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    if result.stdout:
        print(result.stdout, end="")
    return output_path


def _parse_proposals_file(path: Path):
    """Read and leniently parse a proposals JSON file (array of objects)."""
    text = _escape_raw_control_chars_in_json_strings(
        _strip_markdown_fence(Path(path).read_text(encoding="utf-8")))
    proposals, _dropped = _parse_proposals_lenient(text)
    if not isinstance(proposals, list):
        raise ValueError(f"Proposals file must be a JSON array: {path}")
    return proposals


def gen_proposals_obo(sql_path: Path, opts: DbOptions, stat_path: Path = None,
                      explain_path: Path = None, output_path: Path = None,
                      proposal_count: int = PROPOSAL_COUNT) -> Path:
    """Generate proposals by calling proposal_one_pg.py ``proposal_count`` times.

    proposal_one_pg.py returns a single-element JSON array each run. This invokes
    it repeatedly, collects every proposal object, and writes one combined JSON
    array to ``output_path`` in the same format produced by ``gen_proposals``.
    By default reads stat/explain from ``data/stat``/``data/explain`` and writes
    the combined result to ``data/obo_proposal``. Returns the output path.
    """
    stat_path = Path(stat_path) if stat_path else stat_default_path(sql_path, opts.database)
    explain_path = Path(explain_path) if explain_path else explain_default_path(sql_path, opts.database)
    output_path = Path(output_path) if output_path else obo_proposal_default_path(sql_path, opts.database)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    combined = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i in range(1, proposal_count + 1):
            tmp_path = Path(tmp_dir) / f"{sql_path.stem}_proposal_{i}.json"
            cmd = [
                sys.executable, str(PROPOSAL_ONE_PG_SCRIPT),
                "--sql", str(sql_path),
                "--stat", str(stat_path),
                "--explain", str(explain_path),
                "--output", str(tmp_path),
            ]
            logger.info(f"generating proposal {i}/{proposal_count} via proposal_one_pg.py ...")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if result.returncode != 0:
                print(f"[ERROR] proposal_one_pg failed: {result.stderr.strip()}", file=sys.stderr)
                sys.exit(1)
            if result.stdout:
                print(result.stdout, end="")

            if not tmp_path.exists():
                logger.warning(f"proposal_one_pg produced no output for run {i}, skipping")
                continue
            try:
                for p in _parse_proposals_file(tmp_path):
                    if isinstance(p, dict):
                        combined.append(p)
            except Exception as e:
                logger.warning(f"Failed to parse proposal run {i}: {e}")

            if i < proposal_count:
                time.sleep(3.0)

    for idx, p in enumerate(combined, 1):
        p["proposal_id"] = idx

    output_path.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info(f"Combined {len(combined)} proposal(s) written to: {output_path}")
    return output_path


def gen_proposals_obo_for_sql(sql_path: Path, opts: DbOptions,
                              output_dir: Path = None,
                              proposal_count: int = PROPOSAL_COUNT) -> Path:
    """Generate OBO proposals for a single SQL file.

    Reuses pre-existing stat/explain artifacts (read from ``data/stat`` and
    ``data/explain`` respectively) and calls ``proposal_one_pg.py`` repeatedly,
    combining the single-proposal arrays into one JSON array written to
    ``data/obo_proposal/{db_dir}/``. When ``output_dir`` is provided, the
    combined proposal is written flat into that directory instead.
    """
    sql_path = Path(sql_path)
    logger.info(f"=== Generating OBO proposals for {sql_path.name} ===")

    if output_dir is None:
        proposals_path = gen_proposals_obo(sql_path, opts,
                                           proposal_count=proposal_count)
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        proposals_path = gen_proposals_obo(
            sql_path, opts,
            output_path=output_dir / f"{sql_path.stem}_proposals.json",
            proposal_count=proposal_count)

    return proposals_path


def run_one_query(sql_path: Path, opts: DbOptions, output_file = None):
    """Full pipeline for a single SQL file: explain -> stat -> proposals -> run.
    
    Returns the list of result dicts from ``run_proposals`` (empty on failure).
    """
    sql_path = Path(sql_path)
    logger.info(f"=== Processing {sql_path.name} ===")

    logger.info("Step 1/4: Generating EXPLAIN ...")
    explain_path = gen_explain(sql_path, opts)

    logger.info("Step 2/4: Generating statistics ...")
    stat_path = gen_stat(sql_path, opts)

    logger.info("Step 3/4: Generating proposals ...")
    proposals_path = gen_proposals(sql_path, opts, stat_path=stat_path, explain_path=explain_path)

    logger.info("Step 4/4: Running proposals ...")
    return run_proposals(sql_path, opts, proposals_path=proposals_path,
                         output_file=output_file, header=sql_path.name)


def cmd_run_one_query(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_file = open(output_path, "w", encoding="utf-8")
    try:
        run_one_query(sql_path, opts, output_file=output_file)
    finally:
        output_file.close()
    print(f"[INFO] Summary written to: {output_path}")


def discover_sql_files(directory: Path):
    """Recursively find all .sql files under directory, sorted by relative path."""
    return sorted(directory.rglob("*.sql"))


def run_queries(directory: Path, opts: DbOptions, output_path: Path = None,
                stat_path: Path = None) -> None:
    """Run the full pipeline for every SQL file under directory (recursive)."""
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    output_path = Path(output_path) if output_path else DATA_DIR / "run_queries_result.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_file = open(output_path, "w", encoding="utf-8")

    stat_path = Path(stat_path) if stat_path else DATA_DIR / "run_queries_stat.txt"

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Summary output: {output_path}")
    all_results = []
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path} ---")
            try:
                results = run_one_query(sql_path, opts, output_file=output_file)
                all_results.append({"sql_name": sql_path.name, "results": results})
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        output_file.close()
    print(f"[INFO] Summary written to: {output_path}")

    _generate_stat_table(all_results, stat_path)
    print(f"[INFO] Stat summary written to: {stat_path}")


def cmd_run_queries(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_queries(Path(args.dir), opts, output_path=args.output,
                stat_path=args.stat)


def run_proposals_all(directory: Path, opts: DbOptions, output_path: Path = None,
                      stat_path: Path = None, proposals_kind: str = "proposal") -> None:
    """For each .sql file under directory (recursive), call run_proposals and
    print/save a timing table prefixed with the SQL file's basename.

    Reuses ``discover_sql_files`` for recursive lookup and ``run_proposals`` for
    per-file benchmarking. Differs from ``run_queries`` in that it does NOT
    regenerate explain/stat/proposals — it assumes those artifacts already exist
    (i.e. steps 1–3 have been done previously, e.g. by a prior ``run_queries``
    pass). ``proposals_kind`` selects the proposals source and defaults the
    summary/stat output filenames accordingly (``"_obo"`` suffix).
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    tag = "_obo" if proposals_kind == "obo_proposal" else ""

    output_path = (Path(output_path) if output_path
                   else output_dir_for(opts.database) / f"run_proposals_all{tag}_result.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_file = open(output_path, "w", encoding="utf-8")

    stat_path = (Path(stat_path) if stat_path
                 else output_dir_for(opts.database) / f"run_proposals_all{tag}_stat.txt")

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Summary output: {output_path}")
    all_results = []
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
            try:
                results = run_proposals(sql_path, opts, output_file=output_file,
                                        header=sql_path.name,
                                        proposals_kind=proposals_kind)
                rank_best_id = _load_rank_best_id(sql_path, opts.database, proposals_kind)
                all_results.append({"sql_name": sql_path.name, "results": results,
                                    "rank_best_id": rank_best_id})
            except SystemExit:
                # run_proposals exits on missing/invalid proposals file; surface
                # the error but keep processing the remaining files.
                logger.error(f"Failed to process {sql_path}: see error above")
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        output_file.close()
    print(f"[INFO] Summary written to: {output_path}")

    _generate_stat_table(all_results, stat_path)
    print(f"[INFO] Stat summary written to: {stat_path}")


def cmd_run_proposals_all(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                      database=args.database, sleep=args.sleep)
    run_proposals_all(Path(args.dir), opts, output_path=args.output,
                      stat_path=args.stat, proposals_kind="proposal")


def cmd_run_proposals_obo(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_proposals(sql_path, opts, proposals_path=args.proposals,
                  output_path=args.output, proposals_kind="obo_proposal")


def cmd_run_proposals_all_obo(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                      database=args.database, sleep=args.sleep)
    run_proposals_all(Path(args.dir), opts, output_path=args.output,
                      stat_path=args.stat, proposals_kind="obo_proposal")


def run_test_lero(sql_path: Path, opts: DbOptions) -> dict:
    """Run warmup + baseline + lero for a single SQL file.

    Reuses ``run_one_proposal`` for execution/timing. The warmup run is
    discarded; baseline and lero results are recorded. Returns a dict with the
    per-query summary fields consumed by ``_generate_lero_stat_table``.
    """
    sql_path = Path(sql_path)
    sql_content = sql_path.read_text(encoding="utf-8").strip()

    logger.info(f"Warmup for {sql_path.name}...")
    run_one_proposal(-1, "warmup", "", sql_content, opts)
    time.sleep(opts.sleep)

    logger.info(f"Running baseline for {sql_path.name}...")
    baseline_res = run_one_proposal(0, "baseline", "", sql_content, opts)
    time.sleep(opts.sleep)

    logger.info(f"Running lero for {sql_path.name}...")
    lero_sql = f"SET enable_lero TO True;\n{sql_content}"
    lero_res = run_one_proposal(1, "lero", "", lero_sql, opts)
    time.sleep(opts.sleep)

    baseline_ms = baseline_res["elapsed_ms"] if baseline_res["status"] == "ok" else None
    lero_ms = lero_res["elapsed_ms"] if lero_res["status"] == "ok" else None

    return {
        "sql_name": sql_path.name,
        "baseline_ms": baseline_ms,
        "lero_ms": lero_ms,
        "lero_status": lero_res["status"],
        "lero_error": lero_res.get("error_msg", ""),
    }


def test_lero(directory: Path, opts: DbOptions, stat_path: Path = None) -> None:
    """Run warmup + baseline + lero for every SQL file under directory (recursive).

    Reuses ``discover_sql_files`` for recursive lookup and ``run_test_lero`` for
    per-file execution. Sleeps ``opts.sleep`` between files to avoid hammering
    the DB. Aggregates into ``lero_{database}_stat.txt`` (or ``--output``).
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    stat_path = Path(stat_path) if stat_path else DATA_DIR / f"lero_{opts.database}_stat.txt"

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    all_results = []
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
            try:
                all_results.append(run_test_lero(sql_path, opts))
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        pass

    _generate_lero_stat_table(all_results, stat_path)
    print(f"[INFO] Lero stat summary written to: {stat_path}")


def run_test_hybridqo(sql_path: Path, opts: DbOptions) -> dict:
    """Run warmup + baseline + HybridQO for a single SQL file.

    Reuses ``run_one_proposal`` for execution/timing. The warmup run is
    discarded; baseline and HybridQO results are recorded. Returns a dict with the
    per-query summary fields consumed by ``_generate_hybridqo_stat_table``.
    """
    sql_path = Path(sql_path)
    sql_content = sql_path.read_text(encoding="utf-8").strip()
    sql_stem = sql_path.stem

    # Database to db_dir mapping for hint file lookup
    db_to_dir = {
        "tpch": "tpch",
        "dsb_10": "tpcds",
        "imdb": "imdb"
    }
    db_dir = db_to_dir.get(opts.database, opts.database)
    
    # Read hint from ~/relation-baselines/HyperQO/hint/{db_dir}/{sql_stem}.hint
    hint_home = Path.home() / "relation-baselines" / "HyperQO" / "hint" / db_dir
    hint_file = hint_home / f"{sql_stem}.hint"
    hint = ""
    hint_found = False
    if hint_file.exists():
        hint = hint_file.read_text(encoding="utf-8").strip()
        hint_found = True
        logger.info(f"Loaded hint from {hint_file}")
    else:
        logger.info(f"Hint file not found: {hint_file}, will skip HybridQO execution")

    logger.info(f"Warmup for {sql_path.name}...")
    run_one_proposal(-1, "warmup", "", sql_content, opts)
    time.sleep(opts.sleep)

    logger.info(f"Running baseline for {sql_path.name}...")
    baseline_res = run_one_proposal(0, "baseline", "", sql_content, opts)
    time.sleep(opts.sleep)

    # If no hint found, skip HybridQO execution and use baseline time
    if not hint_found:
        logger.info(f"Skipping HybridQO for {sql_path.name} (no hint)")
        baseline_ms = baseline_res["elapsed_ms"] if baseline_res["status"] == "ok" else None
        return {
            "sql_name": sql_path.name,
            "baseline_ms": baseline_ms,
            "hybridqo_ms": baseline_ms,  # Use baseline time
            "hybridqo_status": "no hint",
            "hybridqo_error": "",
        }

    logger.info(f"Running HybridQO for {sql_path.name}...")
    hybridqo_sql = f"{hint}\n{sql_content}"
    hybridqo_res = run_one_proposal(1, "hybridqo", "", hybridqo_sql, opts)
    time.sleep(opts.sleep)

    baseline_ms = baseline_res["elapsed_ms"] if baseline_res["status"] == "ok" else None
    
    # Record HybridQO time even if there's a hint error
    # But don't record time if there's a general error (not hint_error)
    hybridqo_status = hybridqo_res["status"]
    if hybridqo_status == "error":
        hybridqo_ms = None  # Don't record time for general errors
    else:
        hybridqo_ms = hybridqo_res.get("elapsed_ms")

    return {
        "sql_name": sql_path.name,
        "baseline_ms": baseline_ms,
        "hybridqo_ms": hybridqo_ms,
        "hybridqo_status": hybridqo_status,
        "hybridqo_error": hybridqo_res.get("error_msg", ""),
    }


def test_hybridqo(directory: Path, opts: DbOptions, stat_path: Path = None) -> None:
    """Run warmup + baseline + HybridQO for every SQL file under directory (recursive).

    Reuses ``discover_sql_files`` for recursive lookup and ``run_test_hybridqo`` for
    per-file execution. Sleeps ``opts.sleep`` between files to avoid hammering
    the DB. Aggregates into ``hybridqo_{database}_stat.txt`` (or ``--output``).
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    stat_path = Path(stat_path) if stat_path else DATA_DIR / f"hybridqo_{opts.database}_stat.txt"

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    all_results = []
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
            try:
                all_results.append(run_test_hybridqo(sql_path, opts))
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        pass

    _generate_hybridqo_stat_table(all_results, stat_path)
    print(f"[INFO] HybridQO stat summary written to: {stat_path}")


def _generate_hybridqo_stat_table(results: list[dict], stat_path: Path) -> None:
    """Generate a summary table for the ``test-hybridqo`` command.

    For each query (identified by ``"sql_name"``), records baseline time,
    HybridQO time, HybridQO-vs-baseline speedup, HybridQO status and HybridQO error.

    Writes a formatted table to ``stat_path`` with columns:
      Query | Baseline(ms) | HybridQO(ms) | Speedup | Status | Error
    """
    stat_path = Path(stat_path)
    stat_path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["Query", "Baseline(ms)", "HybridQO(ms)", "Speedup", "Status", "Error"]
    rows = []

    for r in results:
        sql_name = r["sql_name"]
        baseline_ms = r.get("baseline_ms")
        hybridqo_ms = r.get("hybridqo_ms")
        status = r.get("hybridqo_status", "")
        error = r.get("hybridqo_error", "")
        if len(error) > 40:
            error = error[:37] + "..."

        bl_str = f"{baseline_ms:.2f}" if baseline_ms else "N/A"
        hybridqo_str = f"{hybridqo_ms:.2f}" if hybridqo_ms else "N/A"
        
        # If status is 'no hint', speedup is 1.00x
        if status == "no hint":
            speedup = "1.00x"
        else:
            speedup = f"{baseline_ms / hybridqo_ms:.2f}x" if (baseline_ms and hybridqo_ms) else "N/A"

        rows.append([sql_name, bl_str, hybridqo_str, speedup, status, error])

    if not rows:
        logger.info("No query results to summarize.")
        return

    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)

    lines = [fmt.format(*headers), sep]
    for row in rows:
        lines.append(fmt.format(*row))

    text = "\n".join(lines) + "\n"
    stat_path.write_text(text, encoding="utf-8")
    logger.info(f"HybridQO stat summary written to: {stat_path}")


def cmd_test_hybridqo(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    output_path = Path(args.output) if args.output else None
    test_hybridqo(Path(args.dir), opts, stat_path=output_path)


def cmd_test_lero(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    output_path = Path(args.output) if args.output else None
    test_lero(Path(args.dir), opts, stat_path=output_path)


def gen_proposals_for_sql(sql_path: Path, opts: DbOptions,
                          output_dir: Path = None) -> Path:
    """Generate proposals JSON for a single SQL file (steps 1-3 of the pipeline).

    Executes:
      1. gen_explain   → data/explain/{db_dir}/{stem}_explain.txt
      2. gen_stat      → data/stat/{db_dir}/{stem}_stat.json
      3. proposal_pg.py → data/proposal/{db_dir}/{stem}_proposals.json

    When ``output_dir`` is provided, all three files are written flat into that
    directory instead. Returns the path to the generated proposals file.
    """
    sql_path = Path(sql_path)
    logger.info(f"=== Generating proposals for {sql_path.name} ===")

    if output_dir is None:
        logger.info("Step 1/3: Generating EXPLAIN ...")
        explain_path = gen_explain(sql_path, opts)

        logger.info("Step 2/3: Generating statistics ...")
        stat_path = gen_stat(sql_path, opts)

        logger.info("Step 3/3: Generating proposals via proposal_pg.py ...")
        proposals_path = gen_proposals(sql_path, opts,
                                       stat_path=stat_path,
                                       explain_path=explain_path)
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Step 1/3: Generating EXPLAIN ...")
        explain_path = gen_explain(sql_path, opts,
                                   output_path=output_dir / f"{sql_path.stem}_explain.txt")

        logger.info("Step 2/3: Generating statistics ...")
        stat_path = gen_stat(sql_path, opts,
                             output_path=output_dir / f"{sql_path.stem}_stat.json")

        logger.info("Step 3/3: Generating proposals via proposal_pg.py ...")
        proposals_path = gen_proposals(sql_path, opts,
                                       stat_path=stat_path,
                                       explain_path=explain_path,
                                       output_path=output_dir / f"{sql_path.stem}_proposals.json")

    return proposals_path


def cmd_gen_proposals(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database)
    output_dir = Path(args.output) if args.output else None
    result = gen_proposals_for_sql(sql_path, opts, output_dir=output_dir)
    print(f"[INFO] Proposals written to: {result}")


def gen_proposals_all(directory: Path, opts: DbOptions,
                      output_dir: Path = None) -> None:
    """Generate proposals JSON for every .sql file under directory (recursive).

    Reuses ``discover_sql_files`` for recursive lookup and
    ``gen_proposals_for_sql`` for per-file processing. Sleeps between
    invocations to avoid hammering the DB during EXPLAIN ANALYZE.
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Proposals output directory: {output_dir or '(default nested data/ structure)'}")
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
            try:
                gen_proposals_for_sql(sql_path, opts, output_dir=output_dir)
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        pass
    print(f"[INFO] All proposals written to: {output_dir or '(default nested data/ structure)'}")


def cmd_gen_proposals_all(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    output_dir = Path(args.output) if args.output else None
    gen_proposals_all(Path(args.dir), opts, output_dir=output_dir)


def cmd_gen_proposals_obo(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database)
    output_dir = Path(args.output) if args.output else None
    result = gen_proposals_obo_for_sql(sql_path, opts, output_dir=output_dir,
                                       proposal_count=args.proposal_count)
    print(f"[INFO] Proposals written to: {result}")


def gen_proposals_obo_all(directory: Path, opts: DbOptions,
                          output_dir: Path = None,
                          proposal_count: int = PROPOSAL_COUNT) -> None:
    """Generate OBO proposals JSON for every .sql file under directory (recursive).

    Mirrors ``gen_proposals_all`` but calls ``gen_proposals_obo_for_sql`` (which
    invokes ``proposal_one_pg.py`` repeatedly).
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Proposals output directory: {output_dir or '(data/obo_proposal/<db_dir>)'}")
    for i, sql_path in enumerate(sql_files, 1):
        logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
        try:
            gen_proposals_obo_for_sql(sql_path, opts, output_dir=output_dir,
                                      proposal_count=proposal_count)
        except Exception as e:
            logger.error(f"Failed to process {sql_path}: {e}")
        if i < len(sql_files):
            time.sleep(opts.sleep)
    print(f"[INFO] All proposals written to: {output_dir or '(data/obo_proposal/<db_dir>)'}")


def cmd_gen_proposals_obo_all(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    output_dir = Path(args.output) if args.output else None
    gen_proposals_obo_all(Path(args.dir), opts, output_dir=output_dir,
                          proposal_count=args.proposal_count)


def rank_proposals_for_sql(sql_path: Path, opts: DbOptions,
                           proposals_kind: str) -> Path:
    """Invoke proposal_rank_pg.py for a single SQL file.

    ``proposals_kind`` is the subdir under ``DATA_DIR`` holding both the input
    proposals and the rank result (``"proposal"`` or ``"obo_proposal"``). Reads
    ``data/{kind}/{db_dir}/{stem}_proposals.json`` and writes the rank result to
    ``data/{kind}/{db_dir}/{stem}_rank.json``. Returns the rank output path.
    """
    sql_path = Path(sql_path)
    db_dir = db_dir_for(opts.database)
    proposals_path = DATA_DIR / proposals_kind / db_dir / f"{sql_path.stem}_proposals.json"
    output_path = DATA_DIR / proposals_kind / db_dir / f"{sql_path.stem}_rank.json"

    if not proposals_path.exists():
        logger.warning(f"Proposals file not found: {proposals_path}; skipping {sql_path.name}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(PROPOSAL_RANK_PG_SCRIPT),
        "--sql", str(sql_path),
        "--proposals", str(proposals_path),
        "--output", str(output_path),
    ]
    logger.info(f"Ranking proposals for {sql_path.name} ...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"[ERROR] proposal_rank_pg failed: {result.stderr.strip()}", file=sys.stderr)
    if result.stdout:
        print(result.stdout, end="")
    return output_path


def rank_proposals_all(directory: Path, opts: DbOptions, proposals_kind: str) -> None:
    """Rank proposals for every .sql file under directory, for one proposal kind."""
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    output_dir = DATA_DIR / proposals_kind / db_dir_for(opts.database)
    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Rank output directory: {output_dir}")
    for i, sql_path in enumerate(sql_files, 1):
        logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
        try:
            rank_proposals_for_sql(sql_path, opts, proposals_kind=proposals_kind)
        except Exception as e:
            logger.error(f"Failed to rank {sql_path}: {e}")
        if i < len(sql_files):
            time.sleep(opts.sleep)
    print(f"[INFO] Rank results written to: {output_dir}")


def cmd_rank_proposals_all(args):
    opts = DbOptions(database=args.database, sleep=args.sleep)
    rank_proposals_all(Path(args.dir), opts, proposals_kind="proposal")


def cmd_rank_proposals_all_obo(args):
    opts = DbOptions(database=args.database, sleep=args.sleep)
    rank_proposals_all(Path(args.dir), opts, proposals_kind="obo_proposal")


def main():
    parser = argparse.ArgumentParser(description="Benchmark utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # gen_explain
    p_gen_explain = subparsers.add_parser("gen_explain", help="Generate EXPLAIN ANALYZE output")
    p_gen_explain.add_argument("--output", type=str, default=None,
                                help="Output file path (default: ./data/explain/{db_dir}/{sql_stem}_explain.txt)")
    p_gen_explain.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_explain.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_explain.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_explain.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_explain.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_explain.set_defaults(func=cmd_gen_explain)

    # gen_stat
    p_gen_stat = subparsers.add_parser("gen_stat", help="Generate metadata & statistics JSON")
    p_gen_stat.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_stat.add_argument("--output", type=str, default=None, help="Output JSON file path (default: ./data/stat/{db_dir}/{sql_stem}_stat.json)")
    p_gen_stat.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_stat.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_stat.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_stat.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_stat.set_defaults(func=cmd_gen_stat)

    # run_proposals
    p_run_proposals = subparsers.add_parser("run_proposals", help="Run proposals and benchmark execution time")
    p_run_proposals.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_run_proposals.add_argument("--proposals", type=str, default=None,
                                 help="Path to proposals JSON file (default: ./data/proposal/{db_dir}/{sql_stem}_proposals.json)")
    p_run_proposals.add_argument("--sleep", type=float, default=3.0,
                                 help="Seconds to sleep between proposals (default: 3.0)")
    p_run_proposals.add_argument("--output", type=str, default=None,
                                 help="Summary table output file path (default: ./data/output/{db_dir}/run_proposals_{sql_stem}_result.txt)")
    p_run_proposals.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals.set_defaults(func=cmd_run_proposals)

    # run_proposals_obo
    p_run_proposals_obo = subparsers.add_parser("run_proposals_obo", help="Run OBO proposals and benchmark execution time")
    p_run_proposals_obo.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_run_proposals_obo.add_argument("--proposals", type=str, default=None,
                                     help="Path to proposals JSON file (default: ./data/obo_proposal/{db_dir}/{sql_stem}_proposals.json)")
    p_run_proposals_obo.add_argument("--sleep", type=float, default=3.0,
                                     help="Seconds to sleep between proposals (default: 3.0)")
    p_run_proposals_obo.add_argument("--output", type=str, default=None,
                                     help="Summary table output file path (default: ./data/output/{db_dir}/run_proposals_obo_{sql_stem}_result.txt)")
    p_run_proposals_obo.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals_obo.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals_obo.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals_obo.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals_obo.set_defaults(func=cmd_run_proposals_obo)

    # run_one_query
    p_run_one_query = subparsers.add_parser("run_one_query", help="Full pipeline for a single SQL file")
    p_run_one_query.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_run_one_query.add_argument("--sleep", type=float, default=3.0,
                                 help="Seconds to sleep between proposals (default: 3.0)")
    p_run_one_query.add_argument("--output", type=str, default=None,
                                 help="Summary table output file path (default: ./data/run_one_query_result.txt)")
    p_run_one_query.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_one_query.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_one_query.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_one_query.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_one_query.set_defaults(func=cmd_run_one_query)

    # run_queries
    p_run_queries = subparsers.add_parser("run_queries", help="Full pipeline for every SQL file in a directory")
    p_run_queries.add_argument("--dir", type=str, required=True, help="Directory containing SQL files (recursive)")
    p_run_queries.add_argument("--output", type=str, default=None,
                               help="Summary table output file path (default: ./data/run_queries_result.txt)")
    p_run_queries.add_argument("--stat", type=str, default=None,
                               help="Stat summary table output file path (default: ./data/run_queries_stat.txt)")
    p_run_queries.add_argument("--sleep", type=float, default=3.0,
                               help="Seconds to sleep between queries (default: 3.0)")
    p_run_queries.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_queries.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_queries.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_queries.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_queries.set_defaults(func=cmd_run_queries)

    # run_proposals_all
    p_run_proposals_all = subparsers.add_parser(
        "run_proposals_all",
        help="Run run_proposals for every SQL file in a directory (recursive); does NOT regenerate explain/stat/proposals",
    )
    p_run_proposals_all.add_argument("--dir", type=str, required=True, help="Directory containing SQL files (recursive)")
    p_run_proposals_all.add_argument("--output", type=str, default=None,
                                     help="Summary table output file path (default: ./data/output/{db_dir}/run_proposals_all_result.txt)")
    p_run_proposals_all.add_argument("--stat", type=str, default=None,
                                     help="Stat summary table output file path (default: ./data/output/{db_dir}/run_proposals_all_stat.txt)")
    p_run_proposals_all.add_argument("--sleep", type=float, default=3.0,
                                     help="Seconds to sleep between SQL files (default: 3.0)")
    p_run_proposals_all.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals_all.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals_all.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals_all.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals_all.set_defaults(func=cmd_run_proposals_all)

    # run_proposals_all_obo
    p_run_proposals_all_obo = subparsers.add_parser(
        "run_proposals_all_obo",
        help="Run run_proposals for every SQL file in a directory (recursive); reads data/obo_proposal/{db_dir}/; does NOT regenerate explain/stat/proposals",
    )
    p_run_proposals_all_obo.add_argument("--dir", type=str, required=True, help="Directory containing SQL files (recursive)")
    p_run_proposals_all_obo.add_argument("--output", type=str, default=None,
                                         help="Summary table output file path (default: ./data/output/{db_dir}/run_proposals_all_obo_result.txt)")
    p_run_proposals_all_obo.add_argument("--stat", type=str, default=None,
                                         help="Stat summary table output file path (default: ./data/output/{db_dir}/run_proposals_all_obo_stat.txt)")
    p_run_proposals_all_obo.add_argument("--sleep", type=float, default=3.0,
                                         help="Seconds to sleep between SQL files (default: 3.0)")
    p_run_proposals_all_obo.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals_all_obo.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals_all_obo.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals_all_obo.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals_all_obo.set_defaults(func=cmd_run_proposals_all_obo)

    # test_lero
    p_test_lero = subparsers.add_parser(
        "test_lero",
        help="Run warmup + baseline + lero (SET enable_lero) for every SQL file in a directory (recursive)",
    )
    p_test_lero.add_argument("--dir", type=str, required=True,
                             help="Directory containing SQL files (recursive)")
    p_test_lero.add_argument("--output", type=str, default=None,
                             help="Stat summary table output file path (default: ./data/lero_{database}_stat.txt)")
    p_test_lero.add_argument("--sleep", type=float, default=3.0,
                             help="Seconds to sleep between SQL files (default: 3.0)")
    p_test_lero.add_argument("--database", type=str, default="dsb_10", help="Database name")
    p_test_lero.add_argument("--host", type=str, default="127.0.0.1", help="PostgreSQL host")
    p_test_lero.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    p_test_lero.add_argument("--user", type=str, default="liujianzhong", help="PostgreSQL user")
    p_test_lero.set_defaults(func=cmd_test_lero)

    # test_hybridqo
    p_test_hybridqo = subparsers.add_parser(
        "test_hybridqo",
        help="Run warmup + baseline + HybridQO (with hints from ~/relation-baselines/HyperQO) for every SQL file in a directory (recursive)",
    )
    p_test_hybridqo.add_argument("--dir", type=str, required=True,
                                 help="Directory containing SQL files (recursive)")
    p_test_hybridqo.add_argument("--output", type=str, default=None,
                                 help="Stat summary table output file path (default: ./data/hybridqo_{database}_stat.txt)")
    p_test_hybridqo.add_argument("--sleep", type=float, default=3.0,
                                 help="Seconds to sleep between SQL files (default: 3.0)")
    p_test_hybridqo.add_argument("--database", type=str, default="dsb_10", help="Database name")
    p_test_hybridqo.add_argument("--host", type=str, default="127.0.0.1", help="PostgreSQL host")
    p_test_hybridqo.add_argument("--port", type=int, default=15432, help="PostgreSQL port")
    p_test_hybridqo.add_argument("--user", type=str, default="postgres", help="PostgreSQL user")
    p_test_hybridqo.set_defaults(func=cmd_test_hybridqo)

    # gen_proposals
    p_gen_proposals = subparsers.add_parser(
        "gen_proposals",
        help="Generate proposals JSON for a single SQL file (explain + stat + proposal_pg)",
    )
    p_gen_proposals.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_proposals.add_argument("--output", type=str, default=None,
                                 help="Output directory for generated files (default: ./data/{explain,stat,proposal}/{db_dir}/)")
    p_gen_proposals.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_proposals.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_proposals.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_proposals.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_proposals.set_defaults(func=cmd_gen_proposals)

    # gen_proposals_all
    p_gen_proposals_all = subparsers.add_parser(
        "gen_proposals_all",
        help="Generate proposals JSON for every SQL file in a directory (recursive)",
    )
    p_gen_proposals_all.add_argument("--dir", type=str, required=True,
                                     help="Directory containing SQL files (recursive)")
    p_gen_proposals_all.add_argument("--output", type=str, default=None,
                                     help="Output directory for generated files (default: ./data/{explain,stat,proposal}/{db_dir}/)")
    p_gen_proposals_all.add_argument("--sleep", type=float, default=3.0,
                                     help="Seconds to sleep between SQL files (default: 3.0)")
    p_gen_proposals_all.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_proposals_all.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_proposals_all.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_proposals_all.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_proposals_all.set_defaults(func=cmd_gen_proposals_all)

    # gen_proposals_obo
    p_gen_proposals_obo = subparsers.add_parser(
        "gen_proposals_obo",
        help="Generate proposals JSON for a single SQL file by calling proposal_one_pg.py repeatedly and combining the results",
    )
    p_gen_proposals_obo.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_proposals_obo.add_argument("--output", type=str, default=None,
                                     help="Output directory for generated proposals (default: ./data/obo_proposal/{db_dir}/)")
    p_gen_proposals_obo.add_argument("--proposal_count", type=int, default=PROPOSAL_COUNT,
                                     help=f"Number of proposal_one_pg.py calls to combine (default: {PROPOSAL_COUNT})")
    p_gen_proposals_obo.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_proposals_obo.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_proposals_obo.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_proposals_obo.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_proposals_obo.set_defaults(func=cmd_gen_proposals_obo)

    # gen_proposals_obo_all
    p_gen_proposals_obo_all = subparsers.add_parser(
        "gen_proposals_obo_all",
        help="Generate proposals JSON for every SQL file in a directory by calling proposal_one_pg.py repeatedly and combining the results",
    )
    p_gen_proposals_obo_all.add_argument("--dir", type=str, required=True,
                                         help="Directory containing SQL files (recursive)")
    p_gen_proposals_obo_all.add_argument("--output", type=str, default=None,
                                         help="Output directory for generated proposals (default: ./data/obo_proposal/{db_dir}/)")
    p_gen_proposals_obo_all.add_argument("--proposal_count", type=int, default=PROPOSAL_COUNT,
                                         help=f"Number of proposal_one_pg.py calls to combine (default: {PROPOSAL_COUNT})")
    p_gen_proposals_obo_all.add_argument("--sleep", type=float, default=3.0,
                                         help="Seconds to sleep between SQL files (default: 3.0)")
    p_gen_proposals_obo_all.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_proposals_obo_all.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_proposals_obo_all.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_proposals_obo_all.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_proposals_obo_all.set_defaults(func=cmd_gen_proposals_obo_all)

    # rank_proposals_all
    p_rank_proposals_all = subparsers.add_parser(
        "rank_proposals_all",
        help="Rank proposals via proposal_rank_pg.py for every SQL file in a directory (recursive); reads data/proposal/{db_dir}/",
    )
    p_rank_proposals_all.add_argument("--dir", type=str, required=True,
                                      help="Directory containing SQL files (recursive)")
    p_rank_proposals_all.add_argument("--sleep", type=float, default=3.0,
                                      help="Seconds to sleep between SQL files (default: 3.0)")
    p_rank_proposals_all.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_rank_proposals_all.set_defaults(func=cmd_rank_proposals_all)

    # rank_proposals_all_obo
    p_rank_proposals_all_obo = subparsers.add_parser(
        "rank_proposals_all_obo",
        help="Rank proposals via proposal_rank_pg.py for every SQL file in a directory (recursive); reads data/obo_proposal/{db_dir}/",
    )
    p_rank_proposals_all_obo.add_argument("--dir", type=str, required=True,
                                          help="Directory containing SQL files (recursive)")
    p_rank_proposals_all_obo.add_argument("--sleep", type=float, default=3.0,
                                          help="Seconds to sleep between SQL files (default: 3.0)")
    p_rank_proposals_all_obo.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_rank_proposals_all_obo.set_defaults(func=cmd_rank_proposals_all_obo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()