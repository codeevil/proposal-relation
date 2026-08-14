import argparse
import json
import logging
import os
import subprocess
import sys
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


def run_psql(sql: str, db: str = PGDATABASE):
    result = subprocess.run(
        [PSQL_BIN, "-h", PGHOST, "-p", str(PGPORT), "-U", PGUSER, "-d", db,
         "-X", "-A", "-t", "-q", "--no-psqlrc"],
        input=sql,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] psql failed: {result.stderr.strip()}", file=sys.stderr)
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

    explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}", db=args.database)

    output_path = Path(args.output) if args.output else DATA_DIR / f"{sql_path.stem}_explain.txt"
    output_path.write_text(explain_output, encoding="utf-8")

    print(f"[INFO] EXPLAIN ANALYZE written to: {output_path}")


def cmd_gen_stat(args):
    sql_path = Path(args.sql)
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    sql_content = sql_path.read_text(encoding="utf-8").strip()
    if not sql_content:
        print(f"[ERROR] SQL file is empty: {sql_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if not output_path:
        output_name = f"{sql_path.stem}_stat.json"
        output_path = str(DATA_DIR / output_name)

    collector = PgMetadataCollector(
        host=args.host, port=args.port, user=args.user, dbname=args.database,
    )
    try:
        collector.collect_all(sql_content)
        collector.export_json(output_path)
    finally:
        collector.close()


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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()