import argparse
import os
import subprocess
import sys
from pathlib import Path

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

    explain_output = run_psql(f"EXPLAIN ANALYZE {sql_content}")

    output_name = f"{sql_path.stem}_explain.txt"
    output_path = DATA_DIR / output_name
    output_path.write_text(explain_output, encoding="utf-8")

    print(f"[INFO] EXPLAIN ANALYZE written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_gen_explain = subparsers.add_parser("gen_explain", help="Generate EXPLAIN ANALYZE output")
    p_gen_explain.add_argument("--sql", type=str, required=True, help="Path to SQL file")
    p_gen_explain.set_defaults(func=cmd_gen_explain)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()