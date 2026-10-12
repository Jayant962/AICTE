# DocuSense: Intelligent Invoice Analysis and Fraud Screening System

IBM SkillsBuild-AICTE-BharatCares (CSRBOX) Machine Learning & Applied AI Internship 2026 - academic prototype.

**Honest status:** the pipeline, UI and 49 unit/integration tests work. **No real public dataset was obtained** and **no
anomaly model is shipped** (see Limitations). Only 5 clearly labelled synthetic invoices are included for demos.
Alerts are prompts for human review, never findings of fraud.

## Problem and objectives
Manual invoice processing is slow and error-prone: wrong totals, missing fields, duplicates, unusual amounts, poor scans.
Objectives: extract fields from PDF/image invoices; validate arithmetic and dates; find exact/near/conflicting duplicates;
add an unsupervised anomaly indicator; combine everything in a transparent human-review view.

## Features
Upload PDF/JPG/PNG with validation | OpenCV preprocessing + Tesseract OCR | rule-based extraction with
extracted/uncertain/missing status and editable values | 7-rule validation (PASS/REVIEW/FAIL) | duplicate detection with
reasons and configurable threshold | Isolation Forest (optional, needs trained model) | screening category with visible
indicators | SQLite persistence | dashboard, investigation filters, CSV/JSON export | evaluation page.
See `docs/architecture.md` and `docs/methodology.md`.

## Windows setup (PowerShell) — verified on Windows 11, Python 3.11.9
1. Install Python 3.10+ (tick "Add to PATH"). Verified with Python 3.11.9.
2. Install Tesseract (the pip package does NOT include it). Two options:
   - **winget (recommended):** `winget install --id UB-Mannheim.TesseractOCR --silent --accept-package-agreements --accept-source-agreements`  
     (installer runs interactively; wait for "Successfully installed")
   - **Manual extract (no admin needed):** Download the `.exe` from https://github.com/UB-Mannheim/tesseract/wiki , extract with 7-Zip to `%LOCALAPPDATA%\Programs\Tesseract-OCR`  
     `& "$env:ProgramFiles\7-Zip\7z.exe" x tesseract-ocr-w64-setup-5.4.0.20240606.exe "-o$env:LOCALAPPDATA\Programs\Tesseract-OCR" -y`
   - `src/ocr_engine.py` auto-detects both `C:\Program Files\Tesseract-OCR` and `%LOCALAPPDATA%\Programs\Tesseract-OCR`.
   - If detection still fails: `$env:TESSERACT_CMD = "C:\path\to\tesseract.exe"` or set it in the app sidebar.
3. Create the environment and run:
```powershell
cd DocuSense
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
python scripts\make_sample_data.py   # synthetic demo files
python -m pytest -q                  # 51 tests should pass
streamlit run app.py
```
Digital PDFs work without Tesseract; images need it. Dashboard -> "Load SYNTHETIC demo records" fills demo charts.

## Datasets and training
`python scripts\download_dataset.py --info` lists SROIE, CORD and FUNSD with URLs. Then
`python scripts\prepare_data.py --sroie data\raw\sroie` (or `--cord`), `python scripts\evaluate_model.py --truth data\processed\ground_truth.csv`,
`python scripts\train_model.py --records data\processed\records.csv --contamination 0.05`
(refuses to train on < 100 scorable records). Dataset scripts are untested on the real data (unreachable at build time).

## Sample workflow
Upload `sample_data/synthetic_003_mismatch.png` -> Extract -> correct if needed -> Run validation (total_consistency FAIL,
"High concern") -> Save -> upload `synthetic_001.png` then `synthetic_004_duplicate_of_001.png` -> exact duplicate flagged.

## Data handling
SQLite `data/docusense.db` stores extracted fields and a 1,500-char text excerpt, not the file. Reset: Dashboard -> Reset,
or delete the file. Not a production accounting system; no enterprise security/compliance claims.

## Known limitations / future work
See `docs/limitations.md`. Future: layout-aware models (LayoutLM/Donut), line items, vendor-history features,
supervised model if labelled data exists, SHAP, multi-language OCR.

## References
SROIE (ICDAR 2019) https://rrc.cvc.uab.es/?ch=13 | CORD https://github.com/clovaai/cord | FUNSD https://guillaumejaume.github.io/FUNSD/ |
Liu, Ting, Zhou (2008) Isolation Forest, ICDM | Tesseract OCR https://github.com/tesseract-ocr/tesseract | RapidFuzz | scikit-learn.
