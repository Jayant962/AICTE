"""Shared helpers: amount/date parsing and text normalisation."""
import hashlib
import re
from datetime import date, datetime

CURRENCY_PATTERNS = [
    (r"₹|\bRs\.?\b|\bINR\b", "INR"),
    (r"\bUSD\b|US\$|\$", "USD"),
    (r"€|\bEUR\b", "EUR"),
    (r"£|\bGBP\b", "GBP"),
    (r"\bRM\b|\bMYR\b", "MYR"),
]

DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y",
    "%d-%m-%y", "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d %b %y", "%b %d, %Y",
    "%B %d, %Y", "%b %d %Y", "%B %d %Y", "%m/%d/%Y",
]

_LEGAL_SUFFIXES = {
    "ltd", "limited", "llc", "inc", "incorporated", "pvt", "private", "co", "corp",
    "corporation", "sdn", "bhd", "llp", "plc", "gmbh",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def normalize_text(text: str) -> str:
    """Collapse whitespace, unify line endings, strip control characters."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_amount(value):
    """Parse '1,234.50', '1.234,50', 'Rs. 99', '(12.00)' -> float, else None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    negative = raw.startswith("-") or (raw.startswith("(") and raw.endswith(")"))
    m = re.search(r"\d[\d.,]*", raw)  # drop currency prefixes such as 'Rs.' or '$'
    if not m:
        return None
    t = m.group(0).rstrip(".,")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):  # 1.234,50
            t = t.replace(".", "").replace(",", ".")
        else:  # 1,234.50
            t = t.replace(",", "")
    elif "," in t:
        parts = t.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            t = parts[0] + "." + parts[1]
        else:
            t = t.replace(",", "")
    elif t.count(".") > 1:
        t = t.replace(".", "")
    try:
        number = float(t)
    except ValueError:
        return None
    return -number if negative else number


def parse_date(value):
    """Parse a date string (day-first preferred for ambiguous numeric dates).
    Returns datetime.date or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = re.sub(r"\s+", " ", str(value).strip().replace("Sept", "Sep"))
    s = s.rstrip(".,")
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def detect_currency(text: str):
    for pattern, code in CURRENCY_PATTERNS:
        if re.search(pattern, text or ""):
            return code
    return None


def normalize_invoice_number(value) -> str:
    """Comparison key: upper-case alphanumerics only."""
    if value is None:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def normalize_vendor(value) -> str:
    if not value:
        return ""
    t = re.sub(r"[^a-z0-9 ]", " ", str(value).lower())
    tokens = [w for w in t.split() if w not in _LEGAL_SUFFIXES]
    return " ".join(tokens)


def to_iso(d):
    return d.isoformat() if isinstance(d, (date, datetime)) else None
