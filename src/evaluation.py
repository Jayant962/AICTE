"""Field-level extraction evaluation against ground truth (only when truth exists)."""
from collections import Counter

from .utils import normalize_vendor, parse_amount, parse_date

EVAL_FIELDS = ["vendor", "invoice_number", "invoice_date", "subtotal", "tax", "total"]


def _norm(field, v):
    if v in (None, ""):
        return None
    if field in ("subtotal", "tax", "total"):
        a = parse_amount(v)
        return None if a is None else round(a, 2)
    if field in ("invoice_date", "due_date"):
        d = parse_date(v)
        return d.isoformat() if d else None
    if field == "vendor":
        return normalize_vendor(v) or None
    return "".join(ch for ch in str(v).upper() if ch.isalnum()) or None


def evaluate_extraction(predictions: list, truths: list, fields=EVAL_FIELDS) -> dict:
    """predictions/truths: aligned lists of flat dicts. Per-field exact match after normalisation.
    precision = correct / predicted-nonempty; recall = correct / truth-nonempty."""
    if len(predictions) != len(truths):
        raise ValueError("predictions and truths must have equal length")
    out = {}
    for f in fields:
        tp = pred_n = truth_n = 0
        for p, t in zip(predictions, truths):
            pv, tv = _norm(f, p.get(f)), _norm(f, t.get(f))
            pred_n += pv is not None
            truth_n += tv is not None
            tp += pv is not None and pv == tv
        out[f] = {"n_truth": truth_n, "n_predicted": pred_n, "correct": tp,
                  "precision": tp / pred_n if pred_n else None,
                  "recall": tp / truth_n if truth_n else None}
    return out


def validation_outcomes(all_results: list) -> dict:
    """Count rule outcomes across many records (descriptive, not a classifier metric)."""
    c = Counter()
    for results in all_results:
        for r in results:
            c[(r["rule"], r["status"])] += 1
    return {f"{k[0]}:{k[1]}": v for k, v in sorted(c.items())}
