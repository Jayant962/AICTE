"""Train the Isolation Forest anomaly model from a records CSV or the local SQLite DB.

  python scripts/train_model.py --records data/processed/records.csv --contamination 0.05
  python scripts/train_model.py --from-db

Refuses to train with < 100 scorable records (total + subtotal + tax). No synthetic padding.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src import database  # noqa: E402
from src.anomaly_detection import DEFAULT_MODEL_PATH, InsufficientDataError, train_anomaly_model  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--records")
    ap.add_argument("--from-db", action="store_true")
    ap.add_argument("--contamination", type=float, default=0.05)
    ap.add_argument("--out", default=DEFAULT_MODEL_PATH)
    a = ap.parse_args()
    if a.records:
        df = pd.read_csv(a.records)
    elif a.from_db:
        conn = database.connect()
        df = pd.DataFrame([r for r in database.fetch_all(conn) if r["source"] != "synthetic_demo"])
    else:
        raise SystemExit("Provide --records CSV or --from-db")
    try:
        art = train_anomaly_model(df, contamination=a.contamination, path=a.out)
    except InsufficientDataError as exc:
        raise SystemExit(f"NOT TRAINED: {exc}")
    print(f"Trained on {art['n_train']} records; saved to {a.out}")
