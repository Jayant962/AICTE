"""Dataset acquisition helper. NO dataset is bundled with DocuSense.

Usage:
  python scripts/download_dataset.py --info            # print manual acquisition steps
  python scripts/download_dataset.py --cord-hf 100     # try ~100 CORD-v2 samples via Hugging Face `datasets`

Status when this project was built: the build sandbox had no access to SROIE, Kaggle or
Hugging Face, so the download paths below are UNTESTED. Follow the manual steps if they fail.
"""
import argparse
import os

INFO = """
Datasets that fit DocuSense (verify licence on the official page before use):

1. SROIE (ICDAR 2019 receipts; OCR + key info: company, date, address, total)
   https://rrc.cvc.uab.es/?ch=13   (registration required for download)
   Place files as: data/raw/sroie/img/*.jpg and data/raw/sroie/entities/*.txt
   Then: python scripts/prepare_data.py --sroie data/raw/sroie

2. CORD v2 (receipts with itemised annotation: subtotal, tax, total)
   https://github.com/clovaai/cord  (licence: CC BY 4.0; full data via Hugging Face 'naver-clova-ix/cord-v2')
   Try: python scripts/download_dataset.py --cord-hf 100

3. FUNSD (form understanding; useful for layout research, not invoice totals)
   https://guillaumejaume.github.io/FUNSD/

None of these contain fraud labels. Anomaly detection therefore stays unsupervised.
Anomaly training additionally needs >= 100 records with total, subtotal AND tax.
"""


def cord_hf(n, out="data/raw/cord"):
    try:
        from datasets import load_dataset  # pip install datasets (optional)
    except ImportError:
        raise SystemExit("Install the optional package first: pip install datasets")
    ds = load_dataset("naver-clova-ix/cord-v2", split=f"train[:{n}]")
    os.makedirs(out, exist_ok=True)
    for i, row in enumerate(ds):
        row["image"].save(os.path.join(out, f"cord_{i:04d}.png"))
        with open(os.path.join(out, f"cord_{i:04d}.json"), "w", encoding="utf-8") as fh:
            fh.write(row["ground_truth"])
    print(f"Saved {len(ds)} CORD-v2 samples to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--cord-hf", type=int, metavar="N")
    a = ap.parse_args()
    if a.cord_hf:
        cord_hf(a.cord_hf)
    else:
        print(INFO)
