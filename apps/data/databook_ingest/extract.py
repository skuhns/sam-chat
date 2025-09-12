from typing import Any, Dict, List, Optional, Tuple
from .utils import to_str
import re
import pandas as pd
import numpy as np
import re

Rect = Tuple[int, int, int, int] 

def _contiguous_segments(bools: List[bool]) -> List[Tuple[int,int]]:
    """Return [ (start,end) ] for contiguous True runs in a boolean list."""
    segs: List[Tuple[int,int]] = []
    s = None
    for i, v in enumerate(bools + [False]):  # sentinel to flush
        if v and s is None:
            s = i
        elif (not v) and s is not None:
            segs.append((s, i-1))
            s = None
    return segs

def find_rectangles(
    df: pd.DataFrame,
    min_header_cells: int = 3,
    gap_rows: int = 1,           # allow up to 1 completely blank row inside a table
    min_rows: int = 2,           # at least header + 1 data row
    outside_tolerance: int = 1,
) -> List[Tuple[int, int, int, int]]:
    """
    - A header row is any row with >= min_header_cells non-empty cells.
    - Split horizontally on header gaps: each contiguous header segment is a table's column window.
    - All segments that start on the SAME header row share the SAME vertical extent (shared_r1).
      We compute shared_r1 using the UNION of all segment windows:
        * If any segment window has inside data -> keep going.
        * Blank rows are tolerated up to `gap_rows`.
        * Rows with data only OUTSIDE all segment windows:
            - if count <= outside_tolerance -> treat as "noise" (counts against gap_rows)
            - else -> stop.
    - Emit a rectangle per segment using (r0, shared_r1, c0, c1).
    """
    nrows, ncols = df.shape
    rects: List[Tuple[int,int,int,int]] = []
    r = 0

    while r < nrows:
        row_vals = [to_str(v) for v in df.iloc[r, :]]
        header_bools = [v != "" for v in row_vals]

        # contiguous header segments with sufficient width
        segs = [seg for seg in _contiguous_segments(header_bools)
                if (seg[1] - seg[0] + 1) >= min_header_cells]

        if not segs:
            r += 1
            continue

        # ---- PASS 1: compute shared_r1 for ALL segments from this header row
        r0 = r
        shared_r1 = r
        blanks_run = 0

        # Precompute union mask function
        def row_inside_any_segment(vals: List[str]) -> bool:
            # inside if ANY non-empty value falls in ANY segment window
            for (c0, c1) in segs:
                for j in range(c0, c1 + 1):
                    if vals[j] != "":
                        return True
            return False

        rr = r + 1
        while rr < nrows:
            vals = [to_str(v) for v in df.iloc[rr, :]]
            row_non_empty_idx = [j for j, v in enumerate(vals) if v != ""]
            row_any = len(row_non_empty_idx) > 0
            inside_any_union = row_inside_any_segment(vals)

            if inside_any_union:
                shared_r1 = rr
                blanks_run = 0
            else:
                if not row_any:
                    # fully blank row -> tolerate up to gap_rows
                    blanks_run += 1
                    if blanks_run <= gap_rows:
                        shared_r1 = rr
                    else:
                        break
                else:
                    # data exists but ONLY outside all segments
                    outside_count = len(row_non_empty_idx)
                    if outside_count <= outside_tolerance:
                        # tolerate as "noise"
                        blanks_run += 1
                        if blanks_run <= gap_rows:
                            shared_r1 = rr
                        else:
                            break
                    else:
                        # significant outside data -> stop
                        break
            rr += 1

        # ---- PASS 2: emit a rect for each segment with the SAME shared_r1
        for (c0, c1) in segs:
            if (shared_r1 - r0 + 1) >= min_rows:
                print("new rec found", r0, shared_r1, c0, c1)
                rects.append((r0, shared_r1, c0, c1))

        # advance to the row after the deepest shared table
        r = shared_r1 + 1

    return rects
# ---------- HEADER INFERENCE ----------
def infer_header_depths(df: pd.DataFrame) -> Tuple[int, int]:
    """
    Infer number of header rows (from top) and header cols (from left).
    Heuristic: rows/cols with majority non-numeric tokens are headers.
    """
    def is_numericish(s: str) -> bool:
        s = s.strip()
        if s == "":
            return False
        # tokens like 1,234, (1,234), 12.3%, -45
        return re.match(r"^\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?$", s) is not None

    # header rows
    header_rows = 0
    for i in range(df.shape[0]):
        row_vals = [to_str(x) for x in df.iloc[i, :].tolist()]
        non_empty = [x for x in row_vals if x != ""]
        if not non_empty:
            break
        numericish = sum(1 for x in non_empty if is_numericish(x))
        textish = len(non_empty) - numericish
        # consider it a header row if at least 60% are non-numeric
        if textish >= 0.6 * len(non_empty):
            header_rows += 1
        else:
            break

    # header cols
    header_cols = 0
    for j in range(df.shape[1]):
        col_vals = [to_str(x) for x in df.iloc[:, j].tolist()]
        non_empty = [x for x in col_vals if x != ""]
        if not non_empty:
            break
        numericish = sum(1 for x in non_empty if is_numericish(x))
        textish = len(non_empty) - numericish
        if textish >= 0.6 * len(non_empty):
            header_cols += 1
        else:
            break

    return header_rows, header_cols




# ---------- UNIT / SCALE DETECTION ----------
# not particularly robust
_UNIT_PATTERNS = [
    (r"\b(in|in\s+thousands|thousands)\b", 1e3),
    (r"\b(in|in\s+hundred thousands|hundred thousands)\b", 1e5),
    (r"\b(in|in\s+millions|millions)\b", 1e6),
    (r"\b(in|in\s+billions|billions)\b", 1e9),
    (r"USD|US\$|\$", 1.0),
]

def _parse_unit_scale(text: str) -> Optional[Tuple[str, float]]:
    """
    Extract (unit_symbol, scale) from a short text snippet.
    - '%' => ('%', 1.0)  (parse_number should handle dividing by 100)
    - '$ in thousands', 'thousands' => ('USD' if $/USD present else 'UNIT', 1e3)
    - '(millions)', 'in millions' => scale 1e6
    - '(billions)', 'in billions' => scale 1e9
    - lone '$' or 'USD' => ('USD', 1.0)
    """
    s = (text or "").strip()
    if not s:
        return None
    slow = s.lower()

    # percent overrides everything
    if "%" in s or re.search(r"\bpercent(age)?\b", slow):
        return ("%", 1.0)

    # scale phrases
    scale = None
    if re.search(r"\b(thousand|thousands)\b", slow):
        scale = 1e3
    elif re.search(r"\b(million|millions)\b", slow):
        scale = 1e6
    elif re.search(r"\b(billion|billions)\b", slow):
        scale = 1e9

    # currency/unit detection
    is_usd = "$" in s or "usd" in slow or "us$" in slow
    if is_usd and scale is None:
        return ("USD", 1.0)
    if is_usd and scale is not None:
        return ("USD", float(scale))
    if scale is not None:
        # scale but no explicit currency; generic unit
        return ("UNIT", float(scale))

    return None

def detect_units_and_scale(full_sheet: pd.DataFrame,
                           rect: Tuple[int, int, int, int]) -> Dict[str, Any]:
    """
    Simple, priority-based unit/scale detection for a table slice.

    PRIORITY (high → low):
      1) ROW HEADER: first column text in each data row (applies to that row to the right)
      2) SECOND ROW (relative index 1): scan only to the LEFT of each column and
         pick the nearest/last unit hint (applies downward for that column to the right)
      3) TOP-LEFT DEFAULT: small TL window of the table (fallback)

    Returns:
      {
        'default': {'unit': <str>, 'scale': <float>, 'evidence': <str>},
        'overrides': [
            {'r': <abs_row>, 'c': <abs_col>, 'unit': <str>, 'scale': <float>, 'evidence': <str>}
        ]
      }
    """
    r0, r1, c0, c1 = rect
    table = full_sheet.iloc[r0:r1+1, c0:c1+1]

    # -------- helper: parse TL default (low priority) --------
    def tl_strings(max_rows=3, max_cols=3) -> List[str]:
        sub = table.iloc[:min(max_rows, table.shape[0]), :min(max_cols, table.shape[1])]
        vals = [str(x).strip() for x in sub.values.flatten()
                if isinstance(x, (str, np.str_)) and str(x).strip()]
        return vals

    default_unit, default_scale, default_evidence = "", 1.0, ""
    for snippet in tl_strings():
        parsed = _parse_unit_scale(snippet)
        if parsed:
            default_unit, default_scale = parsed
            default_evidence = snippet
            break
    if default_unit == "" and default_evidence == "":
        for snippet in tl_strings():
            if "$" in snippet or "USD" in snippet.upper():
                default_unit, default_scale, default_evidence = "USD", 1.0, snippet
                break

    overrides: List[Dict[str, Any]] = []

    # ----------------------------------------------------------------
    # (1) ROW HEADER priority
    # For each data row (i >= 1), check the row-header cell (col 0).
    # If it contains a unit/scale, apply to that row for columns to the right.
    # Anchor at (abs_r = r0+i, abs_c = c0+1) so it affects cells with col >= c0+1 only.
    # ----------------------------------------------------------------
    if table.shape[0] >= 2 and table.shape[1] >= 2:
        for i in range(1, table.shape[0]):  # data rows, since row 0 is col headers
            cell = table.iat[i, 0]
            if isinstance(cell, (str, np.str_)):
                s = cell.strip()
                if s:
                    parsed = _parse_unit_scale(s)
                    if parsed:
                        unit_symbol, scale = parsed
                        overrides.append({
                            'r': r0 + i,
                            'c': c0 + 1,   # start from first data column
                            'unit': unit_symbol,
                            'scale': float(scale),
                            'evidence': s
                        })

    # ----------------------------------------------------------------
    # (2) SECOND ROW (relative row index 1), left-of-column priority
    # For each data column j>=1, look leftwards across row 1 (second row).
    # Use the nearest (rightmost) unit hint found at or to the left of j.
    # Anchor at (abs_r = r0+1, abs_c = c0+j) so it applies downward for that column window.
    # ----------------------------------------------------------------
    if table.shape[0] >= 2 and table.shape[1] >= 2:
        i = 1  # second row (relative)
        row_vals = [table.iat[i, jj] for jj in range(table.shape[1])]
        # precompute nearest-left unit hint for every column
        nearest_left_unit: List[Optional[Tuple[str, float, str]]] = [None] * table.shape[1]
        last_hint: Optional[Tuple[str, float, str]] = None
        for jj in range(table.shape[1]):
            cell = row_vals[jj]
            if isinstance(cell, (str, np.str_)):
                s = cell.strip()
                if s:
                    parsed = _parse_unit_scale(s)
                    if parsed:
                        u, sc = parsed
                        last_hint = (u, float(sc), s)
            nearest_left_unit[jj] = last_hint

        # Emit overrides for data columns only (>=1) where a hint exists to the left
        for j in range(1, table.shape[1]):
            hint = nearest_left_unit[j]
            if hint is None:
                continue
            unit_symbol, scale, evidence = hint
            overrides.append({
                'r': r0 + 1,      # second row is the anchor (applies downward)
                'c': c0 + j,      # this column (and to the right due to >= in resolver)
                'unit': unit_symbol,
                'scale': float(scale),
                'evidence': evidence
            })

    # Sort by (r, c) so the resolver picks the most specific (latest) match
    overrides.sort(key=lambda x: (x['r'], x['c']))

    return {
        'default': {
            'unit': default_unit,
            'scale': float(default_scale),
            'evidence': default_evidence
        },
        'overrides': overrides
    }


def resolve_unit_scale_for_cell(abs_r: int, abs_c: int, meta: Dict[str, Any]) -> Tuple[str, float]:
    """
    Given absolute (row, col) in the sheet and the meta returned by detect_units_and_scale(),
    pick the most specific override whose anchor is top-left of the cell. Otherwise return default.
    """
    chosen_unit = meta['default']['unit']
    chosen_scale = meta['default']['scale']
    for ov in meta['overrides']:
        if abs_r >= ov['r'] and abs_c >= ov['c']:
            chosen_unit = ov['unit']
            chosen_scale = ov['scale']
    return chosen_unit, chosen_scale
    
# ---------- VALUE PARSING ----------
def parse_number_with_status(cell, unit_symbol: str):
    """
    Return (value: Optional[float], status: str).
    status ∈ {'ok','blank','error_code','dash','non_numeric'}
    """
    s0 = to_str(cell)
    if s0 == "":
        return None, "blank"
    s_up = s0.upper()
    if s_up in {"#N/A", "#DIV/0!", "#VALUE!", "NAN"}:
        return None, "error_code"

    s = s0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()

    is_percent = s.endswith("%") or unit_symbol == "%"
    s = s.replace("%", "")
    s = re.sub(r"[$,]", "", s)

    if s in {"-", "—"}:
        return None, "dash"

    try:
        val = float(s)
        if is_percent:
            #TODO how do determine if % is fraction or not?
            #Assume value is a fraction.
            val *= 1
        if neg:
            val = -val
        return val, "ok"
    except ValueError:
        return None, "non_numeric"

# ---------- HEADER PATH BUILDING ----------
YEAR_RE = re.compile(r"^\s*(\d{4})(?:[-/].*)?$")

def _parse_year(cell: object) -> Optional[int]:
    """
    Try to parse a header cell to a year:
      - '2024-12-31', '2024/12/31', '2024-12-31 0:00:00' -> 2024
      - Excel datetimes / pandas Timestamps -> year
      - '2024' -> 2024
    Returns None if not parseable.
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    s = str(cell).strip()
    m = YEAR_RE.match(s)
    if m:
        return int(m.group(1))
    # try pandas to_datetime for true datetime values
    try:
        dt = pd.to_datetime(cell, errors="coerce")
        if pd.notna(dt):
            return int(dt.year)
    except Exception:
        pass
    return None
    
def normalize_year_header_segments(headers: List[str], min_run: int = 3) -> List[str]:
    """
    For each contiguous segment where ALL cells are parseable to a year
    and the sequence increases strictly by +1 between columns, replace
    those headers with just the year string. Leave other headers as-is.

    Only triggers when the pattern *confirms* yearly increment (length >= min_run).
    """
    years = [_parse_year(h) for h in headers]
    parseable = [y is not None for y in years]
    out = headers[:]  # copy

    for start, end in _contiguous_segments(parseable):
        seg_years = years[start:end+1]
        if len(seg_years) < min_run:
            continue
        # confirm strict +1 increments across the whole segment
        diffs = [b - a for a, b in zip(seg_years, seg_years[1:])]
        if all(d == 1 for d in diffs):
            for i in range(start, end + 1):
                out[i] = str(years[i])
        # else: leave untouched (could be monthly or mixed)
    return out

def build_header_paths(table_df: pd.DataFrame, header_rows: int, header_cols: int) -> Tuple[List[str], List[str]]:
    """
    Create column header labels and row header labels by concatenating header tiers.
    """
    # Column headers
    col_headers: List[str] = []
    for j in range(table_df.shape[1]):
        parts = []
        for i in range(min(header_rows, table_df.shape[0])):
            parts.append(to_str(table_df.iat[i, j]))
        label = " | ".join([p for p in parts if p])
        col_headers.append(label)
    col_headers = normalize_year_header_segments(col_headers, min_run=2)
    # Row headers
    row_headers: List[str] = []
    for i in range(table_df.shape[0]):
        parts = []
        for j in range(min(header_cols, table_df.shape[1])):
            parts.append(to_str(table_df.iat[i, j]))
        label = " | ".join([p for p in parts if p])
        row_headers.append(label)
    return col_headers, row_headers

def detect_generic_sheet_heading(full_sheet: pd.DataFrame) -> str:
    """
    Try to find a generic, sheet-level heading in the top-left area.
    Heuristic: a single non-empty text cell in sparse rows/cols; prefer longer phrases.
    """
    best = ""
    best_len = 0
    max_rows, max_cols = min(20, full_sheet.shape[0]), min(12, full_sheet.shape[1])

    for i in range(max_rows):
        row_vals = full_sheet.iloc[i, :max_cols]
        non_empty = [(j, to_str(v)) for j, v in enumerate(row_vals) if to_str(v)]
        if len(non_empty) == 1:  # looks like a lone label row
            _, txt = non_empty[0]
            # avoid obvious numeric-ish rows
            if not re.search(r"\d", txt) and len(txt) > best_len:
                best = txt
                best_len = len(txt)
    return best


def detect_inferred_table_name(full_sheet: pd.DataFrame, rect: Tuple[int,int,int,int], generic_fallback: str) -> str:
    """
    Prefer the text immediately ABOVE the table's top-left (same column or spanning that row).
    If nothing above, try the row above across the table width.
    If still nothing, try a cell immediately LEFT of the top-left.
    Else, use the generic sheet heading.
    """
    r0, r1, c0, c1 = rect

    # 1) direct cell above top-left
    if r0 - 1 >= 0:
        above_direct = to_str(full_sheet.iat[r0-1, c0])
        if above_direct:
            return above_direct

        # 2) any non-empty text in the row above, across the table width (prefer longest)
        candidates = [to_str(x) for x in full_sheet.iloc[r0-1, c0:c1+1].tolist() if to_str(x)]
        if candidates:
            return max(candidates, key=len)

    # 3) left cell of top-left
    if c0 - 1 >= 0:
        left_direct = to_str(full_sheet.iat[r0, c0-1])
        if left_direct:
            return left_direct

    # 4) fallback to generic
    return generic_fallback



# ---------- FACT EXTRACTION ----------
def extract_facts_from_table(full_sheet, rect, sheet_name, file_name, generic_heading="", ):
    r0, r1, c0, c1 = rect
    table = full_sheet.iloc[r0:r1+1, c0:c1+1].copy()

    # units (dict-based)
    meta = detect_units_and_scale(full_sheet, rect)
    # inferred table name

    # headers
    header_rows, header_cols = infer_header_depths(table)
    col_headers, row_headers = build_header_paths(table, header_rows, header_cols)

    # extract
    facts, skipped_counts = [], {"blank":0,"error_code":0,"dash":0,"non_numeric":0}
    for i in range(header_rows, table.shape[0]):
        for j in range(header_cols, table.shape[1]):
            raw = table.iat[i, j]
            abs_r, abs_c = r0 + i, c0 + j
            unit_symbol, scale = resolve_unit_scale_for_cell(abs_r, abs_c, meta)
            val, status = parse_number_with_status(raw, unit_symbol)
            if val is None:
                if status in skipped_counts: skipped_counts[status] += 1
                continue

            facts.append({
                "file": file_name,
                "sheet": sheet_name,
                "table_r0": r0 + 1,
                "table_c0": c0 + 1,
                "row_idx": abs_r + 1,
                "col_idx": abs_c + 1,
                "row_header": row_headers[i],
                "col_header": col_headers[j],
                "raw_text": to_str(raw),
                "unit": unit_symbol,
                "scale": scale,
                "value_real": val * scale,
                "parse_status": status,     
                "inferred_table_name": 'none'   
            })

    return facts