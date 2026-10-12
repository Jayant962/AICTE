"""Numeric features for the anomaly detector.

Only features that are genuinely derivable from extracted fields are used:
  log_total  = log1p(total)
  tax_ratio  = tax / subtotal
A record is 'scorable' only if total > 0, subtotal > 0 and tax >= 0 are all available.
No placeholders or imputed values are fed to the model.
"""
import math

import numpy as np
import pandas as pd

from .utils import parse_amount

FEATURE_NAMES = ["log_total", "tax_ratio"]


def record_features(record: dict):
    """Return dict of features or None if the record is not scorable."""
    total, subtotal, tax = (parse_amount(record.get(k)) for k in ("total", "subtotal", "tax"))
    if total is None or subtotal is None or tax is None:
        return None
    if not (total > 0 and subtotal > 0 and tax >= 0):
        return None
    if not all(math.isfinite(x) for x in (total, subtotal, tax)):
        return None
    return {"log_total": math.log1p(total), "tax_ratio": tax / subtotal}


def build_feature_frame(records) -> pd.DataFrame:
    """records: iterable of dicts or a DataFrame. Returns only scorable rows."""
    if isinstance(records, pd.DataFrame):
        records = records.to_dict("records")
    rows = []
    for r in records:
        f = record_features(r)
        if f is not None:
            rows.append(f)
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    return df.replace([np.inf, -np.inf], np.nan).dropna()
