"""Exact / near / conflicting duplicate detection with explanations.

The component weights below are transparent heuristics, NOT statistically validated.
"""
from rapidfuzz import fuzz

from .utils import normalize_invoice_number, normalize_vendor, parse_amount, parse_date

WEIGHTS = {"invoice_number": 0.30, "vendor": 0.20, "amount": 0.25, "date": 0.10, "text": 0.15}


def _amount_sim(a, b):
    a, b = parse_amount(a), parse_amount(b)
    if a is None or b is None:
        return None
    if abs(a - b) <= 0.01:
        return 100.0
    return 100.0 * max(0.0, 1 - abs(a - b) / max(abs(a), abs(b), 1e-9))


def compare_records(a: dict, b: dict) -> dict:
    """Component similarities (0-100 or None when unavailable) and combined score."""
    ka, kb = normalize_invoice_number(a.get("invoice_number")), normalize_invoice_number(b.get("invoice_number"))
    comp = {
        "invoice_number": fuzz.ratio(ka, kb) if ka and kb else None,
        "vendor": fuzz.token_sort_ratio(normalize_vendor(a.get("vendor")), normalize_vendor(b.get("vendor")))
        if a.get("vendor") and b.get("vendor") else None,
        "amount": _amount_sim(a.get("total"), b.get("total")),
        "date": None,
        "text": None,
    }
    da, db = parse_date(a.get("invoice_date")), parse_date(b.get("invoice_date"))
    if da and db:
        comp["date"] = 100.0 if da == db else 0.0
    ta, tb = (a.get("text_excerpt") or "")[:2000], (b.get("text_excerpt") or "")[:2000]
    if len(ta) > 30 and len(tb) > 30:
        comp["text"] = fuzz.token_sort_ratio(ta, tb)
    avail = {k: v for k, v in comp.items() if v is not None}
    wsum = sum(WEIGHTS[k] for k in avail)
    score = sum(WEIGHTS[k] * v for k, v in avail.items()) / wsum if wsum else 0.0
    return {"score": round(score, 1), "components": comp}


def find_duplicates(record: dict, history: list, threshold: float = 85.0) -> list:
    """Compare `record` against stored `history` rows. Returns matches sorted by score.

    match_type: same_file | exact | conflict | near
      same_file - identical file hash
      exact     - same invoice no., vendor, total and date
      conflict  - same invoice no. + similar vendor but total or date differs
      near      - combined similarity >= threshold
    """
    matches = []
    key = normalize_invoice_number(record.get("invoice_number"))
    for other in history:
        if record.get("id") is not None and other.get("id") == record.get("id"):
            continue
        cmp = compare_records(record, other)
        c, reasons, mtype = cmp["components"], [], None
        if record.get("file_hash") and record.get("file_hash") == other.get("file_hash"):
            mtype, reasons = "same_file", ["Identical file content (same SHA-256 hash)."]
        else:
            same_no = bool(key) and key == normalize_invoice_number(other.get("invoice_number"))
            same_vendor = (c["vendor"] or 0) >= 90
            same_total = c["amount"] == 100.0
            same_date = c["date"] in (100.0, None)
            if same_no and same_vendor and same_total and same_date:
                mtype = "exact"
                reasons = ["Same invoice number, vendor, total and date."]
            elif same_no and same_vendor:
                mtype = "conflict"
                diffs = []
                if not same_total:
                    diffs.append(f"total differs ({record.get('total')} vs {other.get('total')})")
                if c["date"] == 0.0:
                    diffs.append(f"date differs ({record.get('invoice_date')} vs {other.get('invoice_date')})")
                reasons = ["Same invoice number and vendor but " + ("; ".join(diffs) or "other details differ") + "."]
            elif cmp["score"] >= threshold:
                mtype = "near"
                reasons = [f"Combined similarity {cmp['score']} >= threshold {threshold}."]
        if mtype:
            for k, v in c.items():
                if v is not None:
                    reasons.append(f"{k} similarity: {v:.0f}/100")
            matches.append({"match_type": mtype, "score": cmp["score"], "components": c,
                            "reasons": reasons, "other": other})
    order = {"same_file": 0, "exact": 1, "conflict": 2, "near": 3}
    return sorted(matches, key=lambda m: (order[m["match_type"]], -m["score"]))
