from typing import Dict, List, Tuple, Optional
import re
from rapidfuzz import fuzz
from .utils import to_str

KNOWN_SHEETS: Dict[str, List[str]] = {
    "P&L Statement": [
        "p&l", "profit and loss", "profit & loss", "income statement",
        "p and l", "p / l", "pnl", "p & l statement", "profit and loss statement",
        "statement of operations", "consolidated statements of operations",
    ],
    "Quality of Earnings": [
        "quality of earnings", "qoe", "q o e", "q-of-e",
        "quality-of-earnings", "quality of earning",
        "qoe analysis", "quality of earnings analysis",
        "quality of earnings report", "qoe report",
        "quality of earnings schedule", "qoe schedule",
        "earnings quality", "earnings quality analysis",
    ],
    "Working Capital": [
        "working capital", "wc", "working capital schedule",
        "working capital analysis", "working-capital",
        "net working capital", "nwc",
        "working capital bridge", "working capital rollforward",
        "working capital summary",
    ],
    # hypothetical other sheets
    "Balance Sheet": [
        "balance sheet", "statement of financial position",
        "consolidated balance sheets", "financial position",
    ],
    "Cash Flow Statement": [
        "cash flow", "statement of cash flows", "cashflows",
        "consolidated statements of cash flows",
    ],
}

def _norm(s: str) -> str:
    s = to_str(s).lower()
    s = s.replace("&", "and")
    s = re.sub(r"[\s\-_]+", " ", s)
    s = re.sub(r"[^a-z0-9 ()/]", "", s)
    return s.strip()

def best_known_sheet(sheet_name: str, threshold: int = 88) -> Tuple[Optional[str], float, str]:
    """
    Fuzzy-map a raw sheet name to a canonical known sheet label.
    Returns (known_sheet, score, rule) or (None, 0.0, 'no_match').
    """
    raw = _norm(sheet_name)
    best_score = -1.0
    best_canon = None
    for canon, variants in KNOWN_SHEETS.items():
        for v in variants + [canon]:
            sc = fuzz.token_set_ratio(raw, _norm(v))
            if sc > best_score:
                best_score = sc
                best_canon = canon
    if best_score >= threshold:
        return best_canon, float(best_score), "synonym_gate"
    return None, 0.0, "no_match"