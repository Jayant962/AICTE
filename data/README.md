# data/

Acquired dataset: **CORD v2** (Consolidated Receipt Dataset for Post-OCR Parsing).
- Source URL: https://github.com/clovaai/cord and Hugging Face `naver-clova-ix/cord-v2`
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Acquired subset size: 250 receipt samples downloaded via `python scripts/download_dataset.py --cord-hf 250` into `data/raw/cord`.
- Processed: `python scripts/prepare_data.py --cord data/raw/cord` generated `data/processed/ground_truth.csv` and `data/processed/records.csv` (250 rows; 109 records have all three required financial fields: total, subtotal, and tax).
- Fraud labels: None (receipt parsing dataset; anomalies are purely unsupervised).

| Dataset | Use in DocuSense | Fraud labels? | Notes |
|---|---|---|---|
| SROIE (https://rrc.cvc.uab.es/?ch=13) | OCR + vendor/date/total evaluation | No | Registration required; check terms |
| CORD v2 (https://github.com/clovaai/cord) | subtotal/tax/total evaluation, anomaly features | No | CC BY 4.0 per repository; full data via Hugging Face |
| FUNSD (https://guillaumejaume.github.io/FUNSD/) | Layout research only | No | Form understanding, not invoices |

Layout after `prepare_data.py`: `data/processed/ground_truth.csv`, `data/processed/records.csv` (git-ignored).
The SQLite DB `data/docusense.db` is created at first run (git-ignored). Reset it from the Dashboard or delete the file.
Do not commit raw datasets (size and licence).
