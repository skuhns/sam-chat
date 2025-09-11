from dataclasses import dataclass
import pandas as pd
import numpy as np

# ---------- IO ----------
def load_sheet(path: str, sheet: str) -> pd.DataFrame:
    """Read the sheet as raw strings; don't let pandas guess headers."""
    df = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str)
    # Normalize whitespace-only to NaN
    df = df.replace(r"^\s*$", np.nan, regex=True)
    return df
    
@dataclass(frozen=True)
class IngestConfig:
    scan_top_rows: int = 10
    scan_left_cols: int = 6
    min_rows: int = 2
    min_cols: int = 2
    db_path: str = "./db/databook.sqlite"