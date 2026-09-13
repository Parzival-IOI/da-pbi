"""Migrate an Excel workbook to SQLite, one table per sheet."""

import re
import sqlite3
from pathlib import Path

import pandas as pd

EXCEL_PATH = Path(__file__).resolve().parent.parent / "data" / "Sales and Returns.xlsx"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_and_returns.db"


def sanitize_table_name(sheet_name: str) -> str:
    name = re.sub(r"\W+", "_", sheet_name.strip())
    return name.strip("_").lower()


def migrate(excel_path: Path = EXCEL_PATH, db_path: Path = DB_PATH) -> None:
    xl = pd.ExcelFile(excel_path)
    with sqlite3.connect(db_path) as conn:
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            table_name = sanitize_table_name(sheet_name)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"Migrated sheet '{sheet_name}' -> table '{table_name}' ({len(df)} rows)")


if __name__ == "__main__":
    migrate()
