"""Evaluate OCR + field extraction against a ground-truth CSV (columns as in ground_truth.csv).

  python scripts/evaluate_model.py --truth sample_data/ground_truth.csv --images sample_data --label "SYNTHETIC smoke test"
Writes reports/extraction_eval.json. Results are only as meaningful as the labelled data used.
"""
import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.evaluation import evaluate_extraction  # noqa: E402
from src.field_extraction import to_record  # noqa: E402
from src.pipeline import process_document  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--images", default="")
    ap.add_argument("--label", default="unspecified dataset")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=os.path.join("reports", "extraction_eval.json"))
    a = ap.parse_args()
    df = pd.read_csv(a.truth)
    if a.limit:
        df = df.head(a.limit)
    preds, truths, failures = [], [], []
    for r in df.to_dict("records"):
        path = r["file"] if os.path.exists(str(r["file"])) else os.path.join(a.images, str(r["file"]))
        try:
            out = process_document(os.path.basename(path), open(path, "rb").read())
            preds.append(to_record(out["extraction"]))
            truths.append({k: (None if pd.isna(v) else v) for k, v in r.items()})
        except Exception as exc:  # keep going; report failures honestly
            failures.append({"file": path, "error": str(exc)})
    report = {"dataset": a.label, "n_documents": len(preds), "n_failed": len(failures), "failures": failures,
              "metrics": evaluate_extraction(preds, truths) if preds else {},
              "note": "Exact-match after normalisation; not comparable to published benchmarks."}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=2)
    print(json.dumps(report["metrics"], indent=1))
    print(f"Saved {a.out}")
