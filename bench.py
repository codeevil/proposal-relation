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


def cmd_gen_explain(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    sql_content = sql_path.read_text(encoding="utf-8").strip()
    if not sql_content:
        print(f"[ERROR] SQL file is empty: {sql_path}", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}", db=args.database,
    explain_output = run_psql(f"EXPLAIN {sql_content}", db=args.database,
                              host=args.host, port=args.port, user=args.user)

    output_path = Path(args.output) if args.output else DATA_DIR / f"{sql_path.stem}_explain.txt"
    output_path.write_text(explain_output, encoding="utf-8")

    print(f"[INFO] EXPLAIN ANALYZE written to: {output_path}")


def gen_explain(sql_path: Path, opts: DbOptions, output_path: Path = None) -> Path:
    """Generate EXPLAIN ANALYZE output file for a SQL file. Returns output path."""
    sql_content = sql_path.read_text(encoding="utf-8").strip()
    explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}", db=opts.database,
                              host=opts.host, port=opts.port, user=opts.user)

    output_path = output_path or DATA_DIR / f"{sql_path.stem}_explain.txt"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(explain_output, encoding="utf-8")
    logger.info(f"[INFO] EXPLAIN ANALYZE written to: {output_path}")
    return output_path


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


def run_one_proposal(proposal_id: int, label: str, hint: str, sql_content: str, opts: DbOptions):
    """Execute a single proposal (optional hint + SQL) and measure elapsed time in ms."""
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
    for r in results:
        if r["label"] == "baseline" and r["status"] == "ok":
            baseline_ms = r["elapsed_ms"]
            break

    headers = ["Proposal ID", "Label", "Elapsed (ms)", "Speedup", "Status", "Error"]
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
        rows.append([str(r["proposal_id"]), r["label"], elapsed, speedup, r["status"], err])

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
                  output_file = None, header: str = None):
    """Execute baseline + each proposal in the proposals file, print timing table. Returns results."""
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

    results = []

    logger.info("Running baseline (no hint)...")
    results.append(run_one_proposal(0, "baseline", "", sql_content, opts))

    for p in proposals:
        pid = p.get("proposal_id")
        hint = p.get("hint_combination") or ""
        label = f"proposal_{pid}"
        logger.info(f"Running {label}...")
        results.append(run_one_proposal(pid, label, hint, sql_content, opts))
        time.sleep(opts.sleep)

    _print_results_table(results, header=header, output_file=output_file)
    return results


def cmd_run_proposals(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_proposals(sql_path, opts, proposals_path=args.proposals)


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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()