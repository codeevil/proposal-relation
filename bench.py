import argparse
import json
import logging
import os
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
PGDATABASE = "postgres"
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
         "-X", "-A", "-t", "-q", "--no-psqlrc"],
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
                "extracted_columns": {},
            },
            "tables": {},
        }

    def parse_sql(self, sql_text: str):
        logger.info("Parsing SQL with sqlglot...")
        try:
            ast = sqlglot.parse_one(sql_text)
        except Exception as e:
            raise RuntimeError(f"SQL parse failed: {e}")

        self.result["sql_info"]["original_sql"] = sql_text.strip()

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
        self.result["sql_info"]["extracted_columns"] = extracted_columns
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
                   c.relallvisible,
                   c.relkind,
                   pg_table_size(c.oid) AS size_bytes
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
            "relkind": row["relkind"],
            "size_bytes": row["size_bytes"] if row["size_bytes"] is not None else 0,
        }

    def collect_indexes(self, schema: str, table: str) -> list:
        query = """
            SELECT i.relname AS index_name,
                   pg_get_indexdef(idx.indexrelid) AS index_def,
                   am.amname AS index_type,
                   idx.indisunique,
                   idx.indisprimary,
                   idx.indpred IS NOT NULL AS is_partial,
                   pg_relation_size(idx.indexrelid) AS size_bytes,
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
                "index_def": r["index_def"],
                "index_type": r["index_type"],
                "index_columns": r["index_columns"],
                "is_unique": r["indisunique"],
                "is_primary": r["indisprimary"],
                "is_partial": r["is_partial"],
                "size_bytes": r["size_bytes"] if r["size_bytes"] is not None else 0,
            }
            for r in rows
        ]

    def collect_constraints(self, schema: str, table: str) -> list:
        query = """
            SELECT conname AS constraint_name,
                   contype AS constraint_type,
                   pg_get_constraintdef(con.oid) AS constraint_def,
                   conkey,
                   confrelid::regclass::text AS foreign_table
            FROM pg_constraint con
            JOIN pg_class c ON con.conrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s AND c.relname = %s
            ORDER BY conname
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (schema, table))
            rows = cur.fetchall()
        result = []
        for r in rows:
            columns = []
            if r["conkey"]:
                # Resolve attnum to column names
                col_query = """
                    SELECT a.attname FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s AND c.relname = %s
                      AND a.attnum = ANY(%s)
                      AND a.attnum > 0 AND NOT a.attisdropped
                    ORDER BY a.attnum
                """
                with self.conn.cursor() as cur2:
                    cur2.execute(col_query, (schema, table, r["conkey"]))
                    columns = [row[0] for row in cur2.fetchall()]
            result.append({
                "constraint_name": r["constraint_name"],
                "constraint_type": r["constraint_type"],
                "constraint_def": r["constraint_def"],
                "related_columns": columns,
                "foreign_table": r["foreign_table"] if r["constraint_type"] == "f" else None,
            })
        return result

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
                SELECT attname, n_distinct, null_frac, avg_width,
                       most_common_vals::text,
                       most_common_freqs::text,
                       histogram_bounds::text,
                       correlation
                FROM pg_stats
                WHERE schemaname = %s AND tablename = %s AND attname = %s
            """
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (schema, table, col))
                row = cur.fetchone()
            if not row:
                result[col] = None
                continue
            mcv = self._parse_pg_array(row["most_common_vals"])
            mcf = self._parse_pg_array(row["most_common_freqs"])
            hb = self._parse_pg_array(row["histogram_bounds"])
            result[col] = {
                "attname": row["attname"],
                "n_distinct": row["n_distinct"] if row["n_distinct"] is not None else None,
                "null_frac": row["null_frac"] if row["null_frac"] is not None else None,
                "avg_width": row["avg_width"] if row["avg_width"] is not None else None,
                "most_common_vals": mcv if mcv else None,
                "most_common_freqs": mcf if mcf else None,
                "histogram_bounds": hb if hb else None,
                "correlation": row["correlation"] if row["correlation"] is not None else None,
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
            constraints = self.collect_constraints(schema, table)

            # Collect column statistics only for columns involved in the SQL
            sql_columns = extracted_columns.get(full_name, [])
            # Also check if column appears in the table's default schema
            if not sql_columns and schema == "public":
                sql_columns = extracted_columns.get(table, [])
            col_stats = self.collect_column_statistics(schema, table, sql_columns) if sql_columns else {}

            self.result["tables"][full_name] = {
                "table_metadata": table_meta,
                "indexes": indexes,
                "constraints": constraints,
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

    explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}", db=args.database,
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


def run_one_proposal(proposal_id: int, label: str, hint: str, sql_content: str, opts: DbOptions):
    """Execute a single proposal (optional hint + SQL) and measure elapsed time in ms."""
    sql_to_run = f"{hint}\n{sql_content}" if hint else sql_content
    start = time.perf_counter()
    try:
        run_psql(sql_to_run, db=opts.database, host=opts.host, port=opts.port,
                 user=opts.user, raise_on_error=True)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        status = "ok"
    except RuntimeError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        status = "error"
        logger.warning(f"Proposal {label} failed: {e}")
    return {
        "proposal_id": proposal_id,
        "label": label,
        "hint": hint,
        "elapsed_ms": elapsed_ms,
        "status": status,
    }


def _print_results_table(results):
    baseline_ms = None
    for r in results:
        if r["label"] == "baseline" and r["status"] == "ok":
            baseline_ms = r["elapsed_ms"]
            break

    headers = ["Proposal ID", "Label", "Elapsed (ms)", "Speedup", "Status"]
    rows = []
    for r in results:
        if r["status"] == "ok":
            elapsed = f"{r['elapsed_ms']:.2f}"
            speedup = f"{baseline_ms / r['elapsed_ms']:.2f}x" if baseline_ms else "N/A"
        else:
            elapsed = "error"
            speedup = "N/A"
        rows.append([str(r["proposal_id"]), r["label"], elapsed, speedup, r["status"]])

    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)
    print()
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*row))
    print()


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()


def run_proposals(sql_path: Path, opts: DbOptions, proposals_path: Path = None):
    """Execute baseline + each proposal in the proposals file, print timing table. Returns results."""
    sql_content = sql_path.read_text(encoding="utf-8").strip()

    proposals_path = proposals_path or DATA_DIR / f"{sql_path.stem}_proposals.json"
    proposals_path = Path(proposals_path)
    if not proposals_path.exists():
        print(f"[ERROR] Proposals file not found: {proposals_path}", file=sys.stderr)
        sys.exit(1)
    proposals = json.loads(_strip_markdown_fence(proposals_path.read_text(encoding="utf-8")))
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

    _print_results_table(results)
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


def run_one_query(sql_path: Path, opts: DbOptions) -> None:
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
    run_proposals(sql_path, opts, proposals_path=proposals_path)


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


def run_queries(directory: Path, opts: DbOptions) -> None:
    """Run the full pipeline for every SQL file under directory (recursive)."""
    directory = Path(directory)
    if not directory.is_dir():
        print(f"[ERROR] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    sql_files = discover_sql_files(directory)
    if not sql_files:
        print(f"[WARNING] No .sql files found under {directory}")
        return

    logger.info(f"Found {len(sql_files)} SQL file(s) under {directory}")
    for i, sql_path in enumerate(sql_files, 1):
        logger.info(f"--- [{i}/{len(sql_files)}] {sql_path} ---")
        try:
            run_one_query(sql_path, opts)
        except Exception as e:
            logger.error(f"Failed to process {sql_path}: {e}")
        if i < len(sql_files):
            time.sleep(opts.sleep)


def cmd_run_queries(args):
    opts = DbOptions(host=args.host, port=args.port, user=args.user,
                     database=args.database, sleep=args.sleep)
    run_queries(Path(args.dir), opts)


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