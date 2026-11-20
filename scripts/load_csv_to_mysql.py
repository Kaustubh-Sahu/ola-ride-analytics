"""One-off helper: load data/OlaData.csv into MySQL (database OLA, table OlaData).

Usage (PowerShell):
    python scripts/load_csv_to_mysql.py --user root --password YOUR_PASSWORD
Afterwards run sql/OlaDataSQLqueries.sql in MySQL Workbench to create the views.
"""
import argparse
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.types import VARCHAR

CSV = Path(__file__).resolve().parent.parent / "data" / "OlaData.csv"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", required=True)
    ap.add_argument("--database", default="OLA")
    ap.add_argument("--table", default="OlaData")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+", a.database) or not re.fullmatch(r"[A-Za-z0-9_]+", a.table):
        raise SystemExit("Database and table names may only contain letters, numbers and underscores.")

    df = pd.read_csv(CSV, low_memory=False, parse_dates=["Date"])
    server = create_engine(URL.create("mysql+pymysql", a.user, a.password, a.host, a.port))
    with server.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{a.database}`"))
    engine = create_engine(URL.create("mysql+pymysql", a.user, a.password, a.host, a.port, a.database))
    text_cols = {c: VARCHAR(100) for c in df.select_dtypes("object").columns}
    df.to_sql(a.table, engine, if_exists="replace", index=False, chunksize=5000, dtype=text_cols)
    print(f"Loaded {len(df):,} rows into {a.database}.{a.table}")


if __name__ == "__main__":
    main()
