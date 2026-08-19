import argparse
import json
import logging
import os
import re
import subprocess
import sys
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

    output_path = Path(output_path) if output_path else DATA_DIR / f"{sql_path.stem}_explain.txt"
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
    gen_explain(sql_path, opts, output_path=output_path)
    print(f"[INFO] EXPLAIN ANALYZE written to: {output_path or (DATA_DIR / f'{sql_path.stem}_explain.txt')}")


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


def _print_results_table(results, header: str = None, output_file = None):
    baseline_ms = None
    lero_ms = None
    for r in results:
        if r["label"] == "baseline" and r["status"] == "ok":
            baseline_ms = r["elapsed_ms"]
        if r["label"] == "lero-baseline" and r["status"] == "ok":
            lero_ms = r["elapsed_ms"]

    headers = ["Proposal ID", "Label", "Elapsed (ms)", "Speedup", "Speedup-Lero", "Status", "Error"]
    rows = []
    for r in results:
        if r["status"] == "ok":
            elapsed = f"{r['elapsed_ms']:.2f}"
            speedup = f"{baseline_ms / r['elapsed_ms']:.2f}x" if baseline_ms else "N/A"
            speedup_lero = f"{lero_ms / r['elapsed_ms']:.2f}x" if lero_ms else "N/A"
            err = ""
        elif r["status"] == "hint_error":
            elapsed = f"{r['elapsed_ms']:.2f}"
            speedup = f"{baseline_ms / r['elapsed_ms']:.2f}x" if baseline_ms else "N/A"
            speedup_lero = f"{lero_ms / r['elapsed_ms']:.2f}x" if lero_ms else "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        elif r["status"] == "timeout":
            elapsed = "timeout"
            speedup = "N/A"
            speedup_lero = "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        else:
            elapsed = "error"
            speedup = "N/A"
            speedup_lero = "N/A"
            err = r.get("error_msg", "")
            if len(err) > 60:
                err = err[:57] + "..."
        rows.append([str(r["proposal_id"]), r["label"], elapsed, speedup, speedup_lero, r["status"], err])

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


def run_proposals(sql_path: Path, opts: DbOptions, proposals_path: Path = None,
                  output_path: Path = None, output_file = None, header: str = None):
    """Execute baseline + each proposal in the proposals file, print timing table. Returns results.

    The formatted table is written to ``output_path`` (default
    ``./data/run_proposals_result.txt``). Pass ``output_file`` for callers that
    already hold an open file handle (e.g. ``run_proposals_all`` aggregating
    many tables into one file) — when supplied it overrides ``output_path``.
    """
    sql_content = sql_path.read_text(encoding="utf-8").strip()

    proposals_path = proposals_path or DATA_DIR / f"{sql_path.stem}_proposals.json"
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

    if header is None:
        header = sql_path.name

    if output_file is None:
        resolved_output_path = Path(output_path) if output_path else DATA_DIR / "run_proposals_result.txt"
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        own_file = open(resolved_output_path, "w", encoding="utf-8")
        logger.info(f"Summary output: {resolved_output_path}")
    else:
        own_file = None

    results = []

    lero_opts = DbOptions(
        host="127.0.0.1",
        port=5432,
        user="liujianzhong",
        database=opts.database,
    )

    try:
        logger.info("Running baseline (no hint)...")
        results.append(run_one_proposal(0, "baseline", "", sql_content, opts))

        logger.info("Running lero-baseline (SET enable_lero TO True)...")
        lero_sql = f"SET enable_lero TO True;\n{sql_content}"
        results.append(run_one_proposal(1, "lero-baseline", "", lero_sql, lero_opts))

        for p in proposals:
            pid = p.get("proposal_id")
            hint = p.get("hint_combination") or ""
            label = f"proposal_{pid}"
            logger.info(f"Running {label}...")
            results.append(run_one_proposal(pid, label, hint, sql_content, opts))
            time.sleep(opts.sleep)

        sink = output_file if output_file is not None else own_file
        _print_results_table(results, header=header, output_file=sink)
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

    output_path = output_path or DATA_DIR / f"{sql_path.stem}_stat.json"
    output_path = Path(output_path)

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
    stat_path = Path(stat_path) if stat_path else DATA_DIR / f"{sql_path.stem}_stat.json"
    explain_path = Path(explain_path) if explain_path else DATA_DIR / f"{sql_path.stem}_explain.txt"
    output_path = Path(output_path) if output_path else DATA_DIR / f"{sql_path.stem}_proposals.json"

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


def run_one_query(sql_path: Path, opts: DbOptions, output_file = None) -> None:
    """Full pipeline for a single SQL file: explain -> stat -> proposals -> run."""
    sql_path = Path(sql_path)
    logger.info(f"=== Processing {sql_path.name} ===")

    logger.info("Step 1/4: Generating EXPLAIN ...")
    explain_path = gen_explain(sql_path, opts)

    logger.info("Step 2/4: Generating statistics ...")
    stat_path = gen_stat(sql_path, opts)

    logger.info("Step 3/4: Generating proposals ...")
    proposals_path = gen_proposals(sql_path, opts, stat_path=stat_path, explain_path=explain_path)

    logger.info("Step 4/4: Running proposals ...")
    run_proposals(sql_path, opts, proposals_path=proposals_path,
                  output_file=output_file, header=sql_path.name)


def cmd_run_one_query(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_one_query(sql_path, opts)


def discover_sql_files(directory: Path):
    """Recursively find all .sql files under directory, sorted by relative path."""
    return sorted(directory.rglob("*.sql"))


def run_queries(directory: Path, opts: DbOptions, output_path: Path = None) -> None:
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

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Summary output: {output_path}")
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path} ---")
            try:
                run_one_query(sql_path, opts, output_file=output_file)
            except Exception as e:
                logger.error(f"Failed to process {sql_path}: {e}")
            if i < len(sql_files):
                time.sleep(opts.sleep)
    finally:
        output_file.close()
    print(f"[INFO] Summary written to: {output_path}")


def cmd_run_queries(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_queries(Path(args.dir), opts, output_path=args.output)


def run_proposals_all(directory: Path, opts: DbOptions, output_path: Path = None) -> None:
    """For each .sql file under directory (recursive), call run_proposals and
    print/save a timing table prefixed with the SQL file's basename.

    Reuses ``discover_sql_files`` for recursive lookup and ``run_proposals`` for
    per-file benchmarking. Differs from ``run_queries`` in that it does NOT
    regenerate explain/stat/proposals — it assumes those artifacts already exist
    in ``./data/`` (i.e. steps 1–3 have been done previously, e.g. by a prior
    ``run_queries`` pass).
    """
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    output_path = Path(output_path) if output_path else DATA_DIR / "run_proposals_all_result.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_file = open(output_path, "w", encoding="utf-8")

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    logger.info(f"Summary output: {output_path}")
    try:
        for i, sql_path in enumerate(sql_files, 1):
            logger.info(f"--- [{i}/{len(sql_files)}] {sql_path.name} ---")
            try:
                run_proposals(sql_path, opts, output_file=output_file, header=sql_path.name)
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


def cmd_run_proposals_all(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                      database=args.database, sleep=args.sleep)
    run_proposals_all(Path(args.dir), opts, output_path=args.output)


def main():
    parser = argparse.ArgumentParser(description="Benchmark utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # gen_explain
    p_gen_explain = subparsers.add_parser("gen_explain", help="Generate EXPLAIN ANALYZE output")
    p_gen_explain.add_argument("--output", type=str, default=None,
                                help="Output file path (default: ./data/{sql_stem}_explain.txt)")
    p_gen_explain.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_explain.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_explain.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_explain.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_explain.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_explain.set_defaults(func=cmd_gen_explain)

    # gen_stat
    p_gen_stat = subparsers.add_parser("gen_stat", help="Generate metadata & statistics JSON")
    p_gen_stat.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_stat.add_argument("--output", type=str, default=None, help="Output JSON file path (default: ./data/{sql_stem}_stat.json)")
    p_gen_stat.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_gen_stat.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_gen_stat.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_gen_stat.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_gen_stat.set_defaults(func=cmd_gen_stat)

    # run_proposals
    p_run_proposals = subparsers.add_parser("run_proposals", help="Run proposals and benchmark execution time")
    p_run_proposals.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_run_proposals.add_argument("--proposals", type=str, default=None,
                                 help="Path to proposals JSON file (default: ./data/{sql_stem}_proposals.json)")
    p_run_proposals.add_argument("--sleep", type=float, default=3.0,
                                 help="Seconds to sleep between proposals (default: 3.0)")
    p_run_proposals.add_argument("--output", type=str, default=None,
                                 help="Summary table output file path (default: ./data/run_proposals_result.txt)")
    p_run_proposals.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals.set_defaults(func=cmd_run_proposals)

    # run_one_query
    p_run_one_query = subparsers.add_parser("run_one_query", help="Full pipeline for a single SQL file")
    p_run_one_query.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_run_one_query.add_argument("--sleep", type=float, default=3.0,
                                 help="Seconds to sleep between proposals (default: 3.0)")
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
                                     help="Summary table output file path (default: ./data/run_proposals_all_result.txt)")
    p_run_proposals_all.add_argument("--sleep", type=float, default=3.0,
                                     help="Seconds to sleep between SQL files (default: 3.0)")
    p_run_proposals_all.add_argument("--database", type=str, default=PGDATABASE, help="Database name")
    p_run_proposals_all.add_argument("--host", type=str, default=PGHOST, help="PostgreSQL host")
    p_run_proposals_all.add_argument("--port", type=int, default=PGPORT, help="PostgreSQL port")
    p_run_proposals_all.add_argument("--user", type=str, default=PGUSER, help="PostgreSQL user")
    p_run_proposals_all.set_defaults(func=cmd_run_proposals_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()