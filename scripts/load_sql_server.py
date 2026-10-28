"""Load the model CSVs into a local SQL Server database.

Creates the database if needed, runs sql/01_create_star_schema.sql, loads
dimensions then facts with pyodbc fast_executemany, and checks row counts
and revenue/profit totals against the validated model.

Run from the repository root:
    python scripts/load_sql_server.py [--server "localhost\\SQLEXPRESS"] [--data-dir "E:\\SQLData"]
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

import pyodbc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "data" / "model"
SCHEMA_SQL = PROJECT_ROOT / "sql" / "01_create_star_schema.sql"
DATABASE = "MavenMarketDW"
DRIVER = "ODBC Driver 18 for SQL Server"

# Dimensions first so the fact foreign keys resolve.
LOAD_ORDER = [
    ("dim_date", "analytics.DimDate", 737),
    ("dim_customer", "analytics.DimCustomer", 10_281),
    ("dim_product", "analytics.DimProduct", 1_560),
    ("dim_store", "analytics.DimStore", 24),
    ("fact_sales", "analytics.FactSales", 269_720),
    ("fact_returns", "analytics.FactReturns", 7_087),
]
EXPECTED_REVENUE = "1764546.44"
EXPECTED_PROFIT = "1052818.78"
BATCH_SIZE = 20_000


def connect(server: str, database: str) -> pyodbc.Connection:
    return pyodbc.connect(
        f"DRIVER={{{DRIVER}}};SERVER={server};DATABASE={database};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;",
        autocommit=True,
    )


def create_database(server: str, data_dir: str | None) -> None:
    """Create the database if missing, optionally with its files in data_dir."""
    files = ""
    if data_dir:
        folder = data_dir.rstrip("\\")
        files = (
            f" ON (NAME = {DATABASE}, FILENAME = '{folder}\\{DATABASE}.mdf')"
            f" LOG ON (NAME = {DATABASE}_log, FILENAME = '{folder}\\{DATABASE}_log.ldf')"
        )
    with connect(server, "master") as conn:
        conn.execute(f"IF DB_ID('{DATABASE}') IS NULL CREATE DATABASE {DATABASE}{files};")


def run_script(conn: pyodbc.Connection, path: Path) -> None:
    """Run a T-SQL script, splitting on GO lines like SSMS does."""
    for batch in re.split(r"^\s*GO\s*$", path.read_text(encoding="utf-8"), flags=re.M | re.I):
        if batch.strip():
            conn.execute(batch)


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read every value as text so decimals reach SQL Server without float rounding."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        bool_map = {"True": "1", "False": "0"}
        rows = [[bool_map.get(value, value) for value in row] for row in reader]
    return header, rows


def load_table(conn: pyodbc.Connection, csv_name: str, table: str) -> int:
    header, rows = read_rows(MODEL_DIR / f"{csv_name}.csv")
    columns = ", ".join(f"[{name}]" for name in header)
    placeholders = ", ".join("?" for _ in header)
    cursor = conn.cursor()
    cursor.fast_executemany = True
    # Fixed parameter sizes stop fast_executemany from sizing on the first row.
    cursor.setinputsizes([(pyodbc.SQL_WVARCHAR, 200, 0)] * len(header))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    for start in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(sql, rows[start : start + BATCH_SIZE])
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--server", default=r"localhost\SQLEXPRESS")
    parser.add_argument("--data-dir", help="folder for the .mdf/.ldf files (default: server default)")
    args = parser.parse_args()

    create_database(args.server, args.data_dir)
    with connect(args.server, DATABASE) as conn:
        run_script(conn, SCHEMA_SQL)
        print(f"Schema created in {DATABASE} on {args.server}")

        failures = []
        for csv_name, table, expected in LOAD_ORDER:
            started = time.perf_counter()
            load_table(conn, csv_name, table)
            count = conn.execute(f"SELECT COUNT_BIG(*) FROM {table}").fetchval()
            status = "OK" if count == expected else "MISMATCH"
            if count != expected:
                failures.append(f"{table}: {count} rows, expected {expected}")
            print(f"{table:<24} {count:>8,} rows  {time.perf_counter() - started:5.1f}s  {status}")

        revenue, profit = conn.execute(
            "SELECT CAST(SUM(revenue) AS VARCHAR(30)), CAST(SUM(gross_product_profit) AS VARCHAR(30)) "
            "FROM analytics.FactSales"
        ).fetchone()
        print(f"Revenue {revenue} (expected {EXPECTED_REVENUE})")
        print(f"Profit  {profit} (expected {EXPECTED_PROFIT})")
        if revenue != EXPECTED_REVENUE:
            failures.append(f"revenue {revenue}")
        if profit != EXPECTED_PROFIT:
            failures.append(f"profit {profit}")

    if failures:
        raise SystemExit("Load validation failed: " + "; ".join(failures))
    print("Load validation passed")


if __name__ == "__main__":
    main()
