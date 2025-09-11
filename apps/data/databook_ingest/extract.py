from typing import Any, Dict, List, Optional, Tuple
from .utils import to_str
import re
import pandas as pd
import numpy as np
import math

def find_rectangles(df: pd.DataFrame, min_rows: int = 2, min_cols: int = 2) -> List[Tuple[int, int, int, int, Optional[str]]]:
    """
    Return list of (r0, r1, c0, c1, title_evidence) 0-based rectangles.
    If the first row of the trimmed subtable has exactly one non-empty cell,
    use that cell as title_evidence and skip that row (advance r0 by 1).
    """
    mask = df.notna()
    non_empty_rows = mask.any(axis=1).to_list()
    row_blocks: List[Tuple[int, int]] = []
    start = None
    for i, val in enumerate(non_empty_rows + [False]):
        if val and start is None:
            start = i
        elif not val and start is not None:
            row_blocks.append((start, i - 1))
            start = None

    rects: List[Tuple[int, int, int, int, Optional[str]]] = []
    for r0, r1 in row_blocks:
        block = df.iloc[r0 : r1 + 1, :]
        non_empty_cols = block.notna().any(axis=0).to_list()
        cstart = None
        for j, val in enumerate(non_empty_cols + [False]):
            if val and cstart is None:
                cstart = j
            elif not val and cstart is not None:
                cend = j - 1
                sub = block.iloc[:, cstart : cend + 1]
                sub_mask = sub.notna()
                if not sub_mask.values.any():
                    cstart = None
                    continue

                # trim borders
                top = 0
                while top < sub.shape[0] and not sub_mask.iloc[top].any():
                    top += 1
                bottom = sub.shape[0] - 1
                while bottom >= 0 and not sub_mask.iloc[bottom].any():
                    bottom -= 1
                left = 0
                while left < sub.shape[1] and not sub_mask.iloc[:, left].any():
                    left += 1
                right = sub.shape[1] - 1
                while right >= 0 and not sub_mask.iloc[:, right].any():
                    right -= 1

                if bottom >= top and right >= left:
                    # compute absolute coords
                    R0 = r0 + top
                    R1 = r0 + bottom
                    C0 = cstart + left
                    C1 = cstart + right

                    # inspect the first row of the trimmed subtable
                    first_row = sub.iloc[top:top+1, left:right+1]

                    # better way to do this?
                    vals = [to_str(x) for x in first_row.values.flatten()]
                    non_empty_vals = [v for v in vals if v != ""]

                    if len(non_empty_vals) == 1:
                        # Single label row: bump start down by 1
                        R0 += 1  # equivalent to top += 1 in absolute coords
                    # ensure still meets size constraints after possible skip
                    if (R1 - R0 + 1) >= min_rows and (C1 - C0 + 1) >= min_cols:
                        print("new rec found", R0, R1, C0, C1)
                        rects.append((R0, R1, C0, C1))
                cstart = None
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
    Table-local unit/scale detection with inline overrides.

    Returns:
      {
        'default': {'unit': <str>, 'scale': <float>, 'evidence': <str>},
        'overrides': [
            {'r': <abs_row>, 'c': <abs_col>, 'unit': <str>, 'scale': <float>, 'evidence': <str>}
        ]
      }

    Semantics:
    - default applies to the entire table.
    - each override applies to any data cell whose absolute (row >= r and col >= c).
      If multiple overrides match, use the one with the greatest (r, then c) — i.e., the
      most specific bottom-right anchor.
    """
    r0, r1, c0, c1 = rect
    table = full_sheet.iloc[r0:r1+1, c0:c1+1]

    def tl_strings(max_rows=3, max_cols=3) -> List[str]:
        sub = table.iloc[:min(max_rows, table.shape[0]), :min(max_cols, table.shape[1])]
        vals = [str(x).strip() for x in sub.values.flatten() if isinstance(x, (str, np.str_)) and str(x).strip()]
        return vals

    # 1) DEFAULT: look only at the table’s top-left area (not global)
    default_unit, default_scale, default_evidence = "", 1.0, ""
    for snippet in tl_strings():
        parsed = _parse_unit_scale(snippet)
        if parsed:
            default_unit, default_scale = parsed
            default_evidence = snippet
            break
    if default_unit == "" and default_evidence == "":
        # Fallback: if we see any '$' in TL, assume USD, else leave blank
        for snippet in tl_strings():
            if "$" in snippet or "USD" in snippet.upper():
                default_unit, default_scale, default_evidence = "USD", 1.0, snippet
                break

    # 2) INLINE OVERRIDES:
    # Heuristics to find unit “anchor” cells *inside the table* that define units for
    # everything beneath/to-the-right.
    # We scan the first few header-like rows/cols of the table to avoid false positives.
    # You can adjust these caps if needed.
    scan_header_rows = min(6, table.shape[0])
    scan_header_cols = min(6, table.shape[1])

    overrides: List[Dict[str, Any]] = []

    def looks_headerish_row(i: int) -> bool:
        # A row is header-ish if most non-empty cells are non-numeric
        row = table.iloc[i, :]
        vals = [str(x).strip() for x in row if str(x).strip()]
        if not vals:
            return False
        numericish = sum(1 for x in vals if re.match(r"^\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?$", x))
        return (len(vals) - numericish) >= 0.6 * len(vals)

    def looks_headerish_col(j: int) -> bool:
        col = table.iloc[:, j]
        vals = [str(x).strip() for x in col if str(x).strip()]
        if not vals:
            return False
        numericish = sum(1 for x in vals if re.match(r"^\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?$", x))
        return (len(vals) - numericish) >= 0.6 * len(vals)

    headerish_rows = {i for i in range(scan_header_rows) if looks_headerish_row(i)}
    headerish_cols = {j for j in range(scan_header_cols) if looks_headerish_col(j)}

    # Candidate anchors = cells in header-ish rows/cols with a unit hint,
    # especially if the rest of the row/col is sparse (“one record that defines a unit”).
    for i in range(min(scan_header_rows, table.shape[0])):
        for j in range(min(scan_header_cols, table.shape[1])):
            txt = table.iat[i, j]
            if not isinstance(txt, (str, np.str_)):
                continue
            s = txt.strip()
            if not s:
                continue
            parsed = _parse_unit_scale(s)
            if not parsed:
                continue

            # Sparsity cue: the row or column has very few non-empty cells => likely a lone unit marker
            row_vals = [str(x).strip() for x in table.iloc[i, :].tolist() if str(x).strip()]
            col_vals = [str(x).strip() for x in table.iloc[:, j].tolist() if str(x).strip()]
            row_sparse = len(row_vals) <= max(1, math.ceil(0.1 * table.shape[1]))
            col_sparse = len(col_vals) <= max(1, math.ceil(0.1 * table.shape[0]))

            if (i in headerish_rows or j in headerish_cols) or row_sparse or col_sparse:
                unit_symbol, scale = parsed
                overrides.append({
                    'r': r0 + i,            # absolute row in sheet
                    'c': c0 + j,            # absolute col in sheet
                    'unit': unit_symbol,
                    'scale': float(scale),
                    'evidence': s
                })

    # Sort overrides by (r, c) so “nearest bottom-right” is chosen last when resolving
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

    # Row headers
    row_headers: List[str] = []
    for i in range(table_df.shape[0]):
        parts = []
        for j in range(min(header_cols, table_df.shape[1])):
            parts.append(to_str(table_df.iat[i, j]))
        label = " | ".join([p for p in parts if p])
        row_headers.append(label)
    print(row_headers, col_headers)
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
    print("inferring table name", r0, r1, c0,c1)
    if r0 - 1 >= 0:
        above_direct = to_str(full_sheet.iat[r0-1, c0])
        print("above direct", above_direct)
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
def extract_facts_from_table(full_sheet, rect, sheet_name, file_name, generic_heading=""):
    r0, r1, c0, c1 = rect
    print(f"Extracting facts from rect R{r0+1}-{r1+1}, C{c0+1}-{c1+1}")
    table = full_sheet.iloc[r0:r1+1, c0:c1+1].copy()

    # units (dict-based)
    meta = detect_units_and_scale(full_sheet, rect)
    print(f"  Default unit={meta['default']['unit']} scale={meta['default']['scale']} evidence='{meta['default']['evidence']}'")
    if meta['overrides']:
        print(f"  Found {len(meta['overrides'])} inline unit override(s): {[ov['evidence'] for ov in meta['overrides']]}")

    # inferred table name
    inferred_name = detect_inferred_table_name(full_sheet, rect, generic_heading)
    if inferred_name:
        print(f"  Inferred table name: '{inferred_name}'")

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
                "inferred_table_name": inferred_name, 
            })

    print(f"  Extracted {len(facts)} facts; skipped -> {skipped_counts}")
    return facts