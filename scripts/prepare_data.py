"""Convert downloaded datasets into DocuSense ground-truth / records CSVs.

  python scripts/prepare_data.py --sroie data/raw/sroie     -> data/processed/ground_truth.csv
  python scripts/prepare_data.py --cord  data/raw/cord      -> data/processed/ground_truth.csv + records.csv

UNTESTED on the real datasets (not accessible when built); tested only on the file layouts described.
SROIE keys: company, date, address, total. CORD-v2 keys: gt_parse.sub_total / total / menu.
"""
import argparse
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.utils import parse_amount  # noqa: E402

OUT = os.path.join("data", "processed")
FIELDS = ["file", "vendor", "invoice_number", "invoice_date", "due_date", "subtotal", "tax", "total"]


def sroie(root):
    rows = []
    for txt in sorted(glob.glob(os.path.join(root, "entities", "*.txt"))):
        base = os.path.splitext(os.path.basename(txt))[0]
        img = next(iter(glob.glob(os.path.join(root, "img", base + ".*"))), None)
        try:
            d = json.load(open(txt, encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if img:
            rows.append({"file": img, "vendor": d.get("company"), "invoice_date": d.get("date"),
                         "total": parse_amount(d.get("total"))})
    return rows


def cord(root):
    rows = []
    for js in sorted(glob.glob(os.path.join(root, "*.json"))):
        d = json.load(open(js, encoding="utf-8")).get("gt_parse", {})
        img = js[:-5] + ".png"
        st, tt = d.get("sub_total", {}) or {}, d.get("total", {}) or {}
        if isinstance(st, list) or isinstance(tt, list):
            continue
        rows.append({"file": img, "subtotal": parse_amount(st.get("subtotal_price")),
                     "tax": parse_amount(st.get("tax_price")), "total": parse_amount(tt.get("total_price"))})
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sroie")
    ap.add_argument("--cord")
    a = ap.parse_args()
    rows = sroie(a.sroie) if a.sroie else cord(a.cord) if a.cord else None
    if rows is None:
        raise SystemExit("Give --sroie DIR or --cord DIR")
    os.makedirs(OUT, exist_ok=True)
    for name in ("ground_truth.csv", "records.csv"):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")
