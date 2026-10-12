"""Rule-based (regex + layout-order heuristic) invoice field extraction.

This is NOT a trained document-understanding model. It reads OCR text line by line
and applies keyword/regex rules. Every field carries a status:
  extracted  - a rule matched a keyword-anchored value
  uncertain  - value came from a fallback heuristic; verify manually
  missing    - nothing found (never guessed)
"""
import re

from .utils import detect_currency, normalize_text, parse_amount, parse_date, to_iso

FIELD_NAMES = ["vendor", "invoice_number", "invoice_date", "due_date",
               "subtotal", "tax", "total", "currency"]

_AMOUNT_RE = re.compile(r"(?<![\w.])\(?-?\d[\d,]*(?:\.\d{1,2})?\)?(?![\w])")
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent\b|\bx\b|\bpct\b)", re.I)
_DATE_RES = [
    re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"),
    re.compile(r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b"),
    re.compile(r"\b\d{1,2}[ -](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ -,]*\d{2,4}\b", re.I),
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{4}\b", re.I),
]
_INV_NO_RE = re.compile(
    r"(?:invoice|inv|bill|receipt)\s*(?:no\.?|number|num\.?|#|id|:)\s*[:.#\-]*\s*([A-Z0-9][A-Z0-9\-/_.]{2,})",
    re.I)
_TAX_EXCLUDE = re.compile(r"gstin|gst\s*(?:no|reg|id)|tax\s*(?:id|no|reg)|vat\s*(?:no|reg|id)|reg\.?\s*no|invoice|pan\b", re.I)
_VENDOR_SKIP = re.compile(r"invoice|receipt|bill\b|tax|date|page|tel|phone|www\.|@|gst|vat|no\.|#|cash|total", re.I)


def _field(value=None, status="missing", source=None, note=None):
    return {"value": value, "status": status if value not in (None, "") else "missing",
            "source": source, "note": note}


def _amounts_in(line):
    # OCR spacing cleanup: collapse spaces around punctuation (e.g., '36 , 300' -> '36,300')
    cleaned = re.sub(r"(\d)\s*([.,])\s*(\d)", r"\1\2\3", line)
    # OCR spacing cleanup: space thousands separators (e.g., '259 000' -> '259,000')
    cleaned = re.sub(r"\b(\d{1,3})\s+(\d{3})\b", r"\1,\2", cleaned)
    cleaned = _PERCENT_RE.sub(" ", cleaned)
    out = []
    for m in _AMOUNT_RE.finditer(cleaned):
        tok = m.group(0)
        # ignore bare small integers that are likely quantities when no decimal part
        v = parse_amount(tok)
        if v is not None:
            out.append((tok, v))
    return out


def _amount_for(lines, pattern, exclude=None, prefer=None):
    """Return list of (priority, index, value, line) for lines matching pattern."""
    hits = []
    for i, line in enumerate(lines):
        if not re.search(pattern, line, re.I):
            continue
        if exclude and re.search(exclude, line, re.I):
            continue
        amts = _amounts_in(line)
        if not amts and i + 1 < len(lines):
            amts = _amounts_in(lines[i + 1])  # value on the next line
        if not amts:
            continue
        # prefer amounts with decimals when several are present
        dec = [a for a in amts if "." in a[0]]
        value = (dec or amts)[-1][1]
        prio = 1
        if prefer and re.search(prefer, line, re.I):
            prio = 2
        hits.append((prio, i, value, line.strip()))
    return hits


def _extract_total(lines):
    hits = _amount_for(lines, r"total|amount\s*due|balance\s*due|amt\s*due",
                       exclude=r"sub\s*-?\s*total|total\s*tax|tax\s*total|total\s*qty|total\s*items|before\s*tax|excl",
                       prefer=r"grand\s*total|amount\s*due|balance\s*due|total\s*due|net\s*payable|amt\s*due")
    if not hits:
        return _field()
    best = sorted(hits, key=lambda h: (h[0], h[1]))[-1]
    return _field(best[2], "extracted", best[3])


def _extract_subtotal(lines):
    hits = _amount_for(lines, r"sub\s*-?\s*total|total\s*before\s*tax|before\s*tax|taxable\s*(?:value|amount)|net\s*amount|excl\.?\s*(?:tax|gst|vat)")
    if not hits:
        return _field()
    h = hits[0]
    return _field(h[2], "extracted", h[3])


def _extract_tax(lines):
    generic = _amount_for(lines, r"\b(?:tax|vat|gst)\b", exclude=_TAX_EXCLUDE.pattern)
    generic = [h for h in generic if not re.search(r"\b[cust]gst\b|\bigst\b", h[3], re.I)]
    if generic:
        h = generic[-1]
        return _field(h[2], "extracted", h[3])
    parts = _amount_for(lines, r"\b(?:cgst|sgst|utgst|igst)\b", exclude=_TAX_EXCLUDE.pattern)
    if parts:
        return _field(round(sum(p[2] for p in parts), 2), "uncertain",
                      " + ".join(p[3] for p in parts), "Sum of component taxes (CGST/SGST/IGST).")
    return _field()


def _dates_in(line):
    found = []
    for rx in _DATE_RES:
        for m in rx.finditer(line):
            d = parse_date(m.group(0).strip())
            if d:
                found.append((m.start(), d, m.group(0)))
    return [f[1:] for f in sorted(found)]


def _extract_dates(lines):
    inv = due = None
    for line in lines:
        ds = _dates_in(line)
        if not ds:
            continue
        low = line.lower()
        if due is None and re.search(r"due\s*date|payment\s*due|due\s*on|pay\s*by|due\b", low):
            due = _field(to_iso(ds[-1][0]), "extracted", line.strip())
        elif inv is None and re.search(r"invoice\s*date|date\s*of\s*issue|issue\s*date|issued|dated|bill\s*date|\bdate\b", low):
            inv = _field(to_iso(ds[0][0]), "extracted", line.strip())
    if inv is None:
        for line in lines:
            if re.search(r"due", line, re.I):
                continue
            ds = _dates_in(line)
            if ds:
                inv = _field(to_iso(ds[0][0]), "uncertain", line.strip(),
                             "No 'date' keyword found; first date in the document used.")
                break
    return inv or _field(), due or _field()


def _extract_invoice_number(text):
    for m in _INV_NO_RE.finditer(text):
        cand = m.group(1).strip(".-/_")
        if re.search(r"\d", cand) and not parse_date(cand):
            return _field(cand, "extracted", m.group(0).strip())
    return _field()


def _extract_vendor(lines):
    for line in lines[:8]:
        s = line.strip()
        letters = sum(ch.isalpha() for ch in s)
        if len(s) < 3 or letters < 3 or letters / max(len(s), 1) < 0.5:
            continue
        if _VENDOR_SKIP.search(s):
            continue
        return _field(s, "uncertain", s, "Heuristic: first prominent line near the top.")
    return _field()


def extract_fields(raw_text: str) -> dict:
    """Return {'fields': {name: {value,status,source,note}}, 'raw_text': str}."""
    text = normalize_text(raw_text)
    lines = [l for l in text.split("\n") if l.strip()]
    inv_date, due_date = _extract_dates(lines)
    cur = detect_currency(text)
    fields = {
        "vendor": _extract_vendor(lines),
        "invoice_number": _extract_invoice_number(text),
        "invoice_date": inv_date,
        "due_date": due_date,
        "subtotal": _extract_subtotal(lines),
        "tax": _extract_tax(lines),
        "total": _extract_total(lines),
        "currency": _field(cur, "uncertain" if cur == "USD" else "extracted", cur,
                           "'$' alone is ambiguous." if cur == "USD" else None),
    }
    return {"fields": fields, "raw_text": text}


def to_record(extraction: dict) -> dict:
    """Flatten an extraction into {field: value}."""
    return {k: v["value"] for k, v in extraction["fields"].items()}


def completeness(extraction: dict, required=("vendor", "invoice_number", "invoice_date", "total")) -> float:
    f = extraction["fields"]
    return sum(f[k]["status"] != "missing" for k in required) / len(required)
