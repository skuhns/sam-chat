import math
import re
import os
from typing import Any

# ---------- UTILITIES ----------
def ensure_dirs(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def to_str(x: Any) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return str(x).strip()


def percent_like(token: str) -> bool:
    return "%" in token or re.search(r"\bpercent(age)?\b", token.lower()) is not None

