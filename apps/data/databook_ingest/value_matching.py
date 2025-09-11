# databook_ingest/matching.py
from typing import Optional, Tuple, Dict, List
import re
from datetime import date
from rapidfuzz import fuzz, process  # pip install rapidfuzz

from .utils import to_str

# --- Canonical metrics with synonym variants ---
KNOWN_VALUES: Dict[str, List[str]] = {
    "Reported EBITDA": [
        "reported ebitda","ebitda (reported)","ebitda - reported","ebitda reported","ebitda"
    ],
    "Reported EBITDA %": [
        "reported ebitda %","ebitda margin","ebitda %","ebitda % of sales","ebitda percentage"
    ],
    "Net Sales": [
        "net sales","sales","revenue","net revenues","total revenue","net turnover"
    ],
    "Gross Profit": [
        "gross profit","gross income","gross earnings","profit (gross)","gross result"
    ],
    "Net Profit": [
        "net profit","net income","net earnings","earnings","profit after tax","pat","profit (net)"
    ],
    "Gross Margin": [
        "gross margin","gross margin %","gross profit %","gm%","gross margin percent","gross profit margin"
    ],
    "Operating Expense %": [
        "operating expense %","opex %","operating expenses as % of sales","opex ratio","operating expense percentage"
    ],
    "Adjusted EBITDA": [
        "adjusted ebitda","ebitda (adj.)","ebitda adjusted","normalized ebitda","adj. ebitda"
    ],
    "Adjusted EBITDA %": [
        "adjusted ebitda %","adj. ebitda %","adjusted ebitda margin","adj. ebitda margin","adjusted ebitda percentage"
    ],
    "Total Adjustments": [
        "total adjustments","adjustments","ebitda adjustments","total adj.","sum of adjustments"
    ],
    "Adjusted Working Capital": [
        "adjusted working capital","adj. working capital","working capital (adj.)","working capital adjusted"
    ],
    "Reported Working Capital": [
        "reported working capital","working capital","reported wc","wc reported"
    ],
}

# Partition into percent vs non-percent canonicals so unit gating is easy
PERCENT_METRICS = {k for k in KNOWN_VALUES if k.endswith("%") or "percent" in k.lower() or "margin" in k.lower()}
NONPERCENT_METRICS = set(KNOWN_VALUES) - PERCENT_METRICS

def _norm(s: str) -> str:
    s = to_str(s).lower()
    s = re.sub(r"[\s\-\_]+", " ", s)
    s = re.sub(r"[^a-z0-9 %/().,&]", "", s)  # keep % and some punctuation
    return s.strip()

def best_known_value(row_header: str, unit: str, threshold: int = 83) -> Tuple[Optional[str], float, str]:
    """
    Return (canonical_metric, score, rule) or (None, 0.0, 'no_match').
    - Gate by unit: if unit == '%', prefer percent metrics; else prefer non-percent.
    - Uses token_set_ratio which handles word order and extra tokens well.
    """
    rh = _norm(row_header)
    is_pct = (unit == "%") or ("%" in rh) or ("percent" in rh)

    # Candidate canonicals based on unit gate
    candidates = PERCENT_METRICS if is_pct else NONPERCENT_METRICS
    # Build a flat list of (canonical, variant)
    pairs: List[Tuple[str, str]] = []
    for canon in candidates:
        for variant in KNOWN_VALUES[canon]:
            pairs.append((canon, _norm(variant)))

    # Score against all variants; keep the best overall
    best = None
    best_score = -1.0
    best_canon = None
    for canon, variant in pairs:
        score = fuzz.token_set_ratio(rh, variant)
        if score > best_score:
            best_score = score
            best_canon = canon

    if best_score >= threshold:
        return best_canon, float(best_score), ("percent_gate" if is_pct else "unitless")
    # fallback: try the other side if nothing met threshold (helps mis-tagged units)
    if is_pct:
        other = NONPERCENT_METRICS
    else:
        other = PERCENT_METRICS
    pairs = [(canon, _norm(v)) for canon in other for v in KNOWN_VALUES[canon]]
    for canon, variant in pairs:
        score = fuzz.token_set_ratio(rh, variant)
        if score > best_score:
            best_score = score
            best_canon = canon
    if best_score >= threshold:
        return best_canon, float(best_score), ("fallback_other_bucket")
    return None, 0.0, "no_match"

# --- Period parsing from column headers ---

MONTHS = {
    "jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,
    "jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12
}
Q_END = {1:(3,31), 2:(6,30), 3:(9,30), 4:(12,31)}

def parse_known_period(col_header: str) -> Optional[str]:
    """
    Return 'YYYY' or 'YYYY-MM-DD' when we can infer a period from the column header.
    Heuristics:
      - 'FY 2022', '2022' -> '2022'
      - 'Q1 2021' -> '2021-03-31' (quarter end)
      - 'December 31, 2020' -> '2020-12-31'
      - 'Mar-22' -> '2022-03-31' (assume month end)
    """
    s = _norm(col_header)

    # YYYY
    m = re.search(r"\b(20\d{2}|19\d{2})\b", s)
    year = int(m.group(1)) if m else None

    # Quarter
    mq = re.search(r"\bq([1-4])\b.*\b(20\d{2}|19\d{2})\b", s)
    if mq:
        q = int(mq.group(1))
        y = int(mq.group(2))
        mm, dd = Q_END[q]
        return f"{y:04d}-{mm:02d}-{dd:02d}"

    # Month name + optional day + year
    mmatch = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b", s)
    if mmatch and year:
        mm = MONTHS[mmatch.group(0)]
        # explicit day?
        dmatch = re.search(r"\b([12][0-9]|3[01]|0?[1-9])\b", s)
        if dmatch:
            dd = int(dmatch.group(1))
            return f"{year:04d}-{mm:02d}-{dd:02d}"
        # else assume month end (rough)
        # use 30 for simplicity; for pretty you could compute month-end
        return f"{year:04d}-{mm:02d}-28"

    # Plain FY YYYY -> just year
    if re.search(r"\bfy\b", s) and year:
        return f"{year:04d}"

    # Bare year
    if year:
        return f"{year:04d}"

    # mmm-yy like 'Mar-22'
    m2 = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-/](\d{2,4})\b", s)
    if m2:
        mm = MONTHS[m2.group(1)]
        y = int(m2.group(2))
        if y < 100: y += 2000 if y <= 69 else 1900
        return f"{y:04d}-{mm:02d}-28"

    return None

