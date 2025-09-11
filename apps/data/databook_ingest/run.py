
import os
from typing import List, Dict, Any
import pandas as pd

from .extract import detect_generic_sheet_heading, extract_facts_from_table, find_rectangles
from .storage import FACTS_TABLE, init_sqlite, insert_facts, populate_known_facts, populate_known_sheets
from .io_excel import load_sheet


# ---------- CONFIG ----------
INPUT_XLSX = [
    "./databooks/Databook_One_SANITIZED.xlsx",
    "./databooks/Databook_Two_SANITIZED.xlsx",
]
SQLITE_PATH = "./db/databook.sqlite"


def process_workbooks(xlsx_paths: List[str], sqlite_path: str) -> None:
    """Process all sheets in each workbook path."""
    conn = init_sqlite(sqlite_path)
    total_facts = 0

    for xlsx_path in xlsx_paths:
        if not os.path.exists(xlsx_path):
            print(f"[skip] missing file: {xlsx_path}")
            continue

        try:
            xls = pd.ExcelFile(xlsx_path)
            sheet_names = xls.sheet_names
        except Exception as e:
            print(f"[error] could not open {xlsx_path}: {e}")
            continue

        print(f"\n=== Processing workbook: {xlsx_path} ({len(sheet_names)} sheet(s)) ===")
        fname = os.path.basename(xlsx_path)

        for sheet_name in sheet_names:
            print(f"\n-- Sheet: {sheet_name}")
            try:
                df = load_sheet(xlsx_path, sheet_name)
            except Exception as e:
                print(f"[error] load_sheet failed for '{sheet_name}': {e}")
                continue

            rects = find_rectangles(df)
            if not rects:
                print("  No table-like rectangles detected.")
                continue

            generic_heading = detect_generic_sheet_heading(df)

            # Extract & insert per sheet to keep memory bounded
            all_facts: List[Dict[str, Any]] = []
            for rect in rects:
                facts = extract_facts_from_table(df, rect, sheet_name, fname, generic_heading)
                all_facts.extend(facts)

            if all_facts:
                insert_facts(conn, all_facts)
                total_facts += len(all_facts)
                print(f"  Inserted {len(all_facts)} facts from sheet '{sheet_name}'")
            else:
                print("  No facts extracted from this sheet.")

    # done seperately to show that these can be updated and ran as periodic jobs to improve data
    tagged_vals = populate_known_facts(conn, score_threshold=83)
    tagged_sheets = populate_known_sheets(conn, score_threshold=88)

    conn.close()
    print(f"\nDONE. Inserted {total_facts} total fact rows into {sqlite_path} ({FACTS_TABLE}).")
    print(f"Tagged {tagged_vals} facts with known_value/known_period; "
          f"tagged {tagged_sheets} (file, sheet) pairs with known_sheet.")


if __name__ == "__main__":
    process_workbooks(INPUT_XLSX, SQLITE_PATH)