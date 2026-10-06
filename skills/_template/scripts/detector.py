"""Generic 6-signal block detector — configure markers per target, import everywhere.

Copy into a new skill, fill TARGET, and use:
    from detector import TARGET, detect, SUCCESS, PARTIAL
    signal = detect(status, html, TARGET)

Signals: CHALLENGE | THROTTLED | CONSENT_WALL | EMPTY | SUCCESS | PARTIAL | UNKNOWN.
- SUCCESS = data markers present AND price markers present.
- PARTIAL = data markers present but NO inline price (variant-family grid:
  IDs + titles are real, final price lives on detail pages).
- Only SUCCESS / PARTIAL may be parsed. Everything else is a failure —
  climb the ladder, rotate proxy, or cool down.
"""
from typing import Any, Dict, List

SUCCESS = "SUCCESS"
PARTIAL = "PARTIAL"

# --- Fill this per target (see skills/_template/SKILL.md) --------------------
TARGET: Dict[str, Any] = {
    "name": "example",
    "CHALLENGE_MARKERS": ["gokuprops", "awswaf", "challenge.js"],
    "THROTTLE_MARKERS": ["amazonsorry", "request blocked", "captcha-delivery"],
    "CONSENT_MARKERS": ["cookie preferences"],
    "DATA_MARKER": "data-asin",          # substring proving real listing data
    "PRICE_MARKERS": ["a-price-whole", "\u00a3", "&pound;"],
}


def _hits(html_low: str, markers: List[str]) -> bool:
    return any(m.lower() in html_low for m in markers)


def detect(status: int, html: str, target: Dict[str, Any] = TARGET) -> str:
    """Classify a fetch result. `html` may be "" on transport errors."""
    low = (html or "").lower()
    n_data = html.count(str(target.get("DATA_MARKER", "data-asin")))
    if _hits(low, list(target.get("CHALLENGE_MARKERS", []))):
        return "CHALLENGE"
    if status in (429, 503) or _hits(low, list(target.get("THROTTLE_MARKERS", []))):
        return "THROTTLED"
    if status == 200 and n_data == 0:
        if _hits(low, list(target.get("CONSENT_MARKERS", []))):
            return "CONSENT_WALL"
        return "EMPTY"
    if status == 200 and n_data > 0:
        price_markers = list(target.get("PRICE_MARKERS", []))
        if any(pm in html or pm in low for pm in price_markers):
            return SUCCESS
        return PARTIAL
    if status in (202,):
        return "CHALLENGE"
    return "UNKNOWN"
