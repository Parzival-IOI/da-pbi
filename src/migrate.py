"""Migrate an Excel workbook to SQLite, one table per sheet."""

import re
import sqlite3
from pathlib import Path

import pandas as pd

EXCEL_PATH = Path(__file__).resolve().parent.parent / "data" / "Sales and Returns.xlsx"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_and_returns.db"


SALES_DATED_VIEW = """
create view sales_dated as
select s.*,
    SUBSTR(s.Date, -4) || '-' ||
    CASE SUBSTR(s.Date, INSTR(s.Date, ', ') + 2, INSTR(SUBSTR(s.Date, INSTR(s.Date, ', ') + 2), ' ') - 1)
        WHEN 'January'   THEN '01' WHEN 'February' THEN '02' WHEN 'March'     THEN '03'
        WHEN 'April'     THEN '04' WHEN 'May'      THEN '05' WHEN 'June'      THEN '06'
        WHEN 'July'      THEN '07' WHEN 'August'   THEN '08' WHEN 'September' THEN '09'
        WHEN 'October'   THEN '10' WHEN 'November' THEN '11' WHEN 'December'  THEN '12'
    END as year_month
from sales s
"""


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
        conn.execute("drop view if exists sales_dated")
        conn.execute(SALES_DATED_VIEW)
        print("Created view 'sales_dated' (sales + year_month)")


if __name__ == "__main__":
    migrate()
