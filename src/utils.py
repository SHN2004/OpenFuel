import re
from typing import Optional


def clean_price_string(price_str: str) -> Optional[float]:
    """
    Clean a raw price string and convert it to a float.

    Rules (from Story 2.3 acceptance criteria):
    - Standard formats like "96.72" -> 96.72
    - Currency symbols and mis-encoded prefixes like "ƒ,1 96.72", "Rs. 96.72" -> 96.72
    - Commas as thousands separators: "1,200.50" -> 1200.50
    - Leading/trailing whitespace is ignored
    - Returns None for invalid inputs (e.g., "", "N/A", "Free")
    """
    if price_str is None:
        return None

    raw = price_str.strip()
    if not raw:
        return None

    # Normalize known mis-encoded currency prefix from the source site
    raw = raw.replace("ƒ,1", "")

    # Core regex cleaning as specified in the story
    cleaned = re.sub(r"[^\d.]", "", raw)

    # Handle multiple dots:
    # - Accept patterns like ".96.72" that come from "Rs. 96.72" by dropping
    #   the leading dot when the rest is a valid single-decimal number.
    # - Reject ambiguous patterns like "1.2.3".
    if cleaned.count(".") > 1:
        if cleaned.startswith(".") and cleaned[1:].count(".") == 1:
            cleaned = cleaned.lstrip(".")
        else:
            return None

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None
