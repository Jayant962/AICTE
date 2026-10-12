# Submission checklist

## Project materials
- [x] Source code (`src/*.py`, `app.py`, `scripts/*.py`)
- [x] Tests — **51 tests pass** (`python -m pytest -q`, 2026-10-12 on Windows 11)
- [x] Docs — `README.md`, `docs/architecture.md`, `docs/limitations.md`, `docs/methodology.md`, `docs/viva_questions.md`
- [x] Concept note — `docs/concept_note.md` + `docs/concept_note.pdf` (real metrics)
- [x] Lean Canvas — `docs/lean_canvas.md` + `docs/lean_canvas.pdf` (real metrics)
- [x] Slide deck — `docs/DocuSense_Presentation.pptx` (12 slides, real screenshots + metrics)

## Dataset & model
- [x] CORD v2 — 250 receipts downloaded from Hugging Face (`naver-clova-ix/cord-v2`, CC BY 4.0)
- [x] Extraction evaluated on 100 CORD documents → `reports/extraction_eval.json`
- [x] Anomaly model trained on 109 records → `models/anomaly_model.joblib`
- [x] `data/README.md` documents source, licence, acquisition command and key statistics

## Windows run-through
- [x] Tesseract 5.4.0 (UB-Mannheim) installed and working on Windows 11
- [x] `streamlit run app.py` runs successfully; 7 workflow screenshots captured
- [x] All 51 tests pass end-to-end on Windows (`python -m pytest -q`)

## Screenshots (7 captured, saved to `docs/screenshots/`)
- [x] `01_dashboard.png` — dashboard with synthetic demo records
- [x] `02_upload_and_preview.png` — upload + OCR text preview
- [x] `03_extracted_fields_and_validation.png` — extracted fields + 7-rule validation results
- [x] `04_anomaly_analysis.png` — anomaly score and breakdown
- [x] `05_duplicate_comparison.png` — side-by-side duplicate comparison
- [x] `06_invoice_investigation.png` — investigation / detail view
- [x] `07_model_evaluation.png` — evaluation page with real metrics

## GitHub readiness
- [x] `.gitignore` excludes `.venv/`, `data/raw/`, `data/processed/`, `data/*.db`, `models/*.joblib`, `*.log`, `.env`
- [x] **`LICENSE`** — MIT licence committed
- [x] Verified `git status` — no secrets, DB, raw data, or joblib binaries tracked
- [x] Pushed to GitHub repository: **`https://github.com/Jayant962/AICTE.git`** (main branch)
- [ ] Copy the repository URL into the IBM SkillsBuild submission form

## Internship form (items only YOU can provide)
- [ ] Project GitHub link
- [ ] Concept note (use `docs/concept_note.pdf`)
- [ ] Final presentation (use `docs/DocuSense_Presentation.pptx`)
- [ ] Screenshots (use images in `docs/screenshots/`)
- [ ] **IBM SkillsBuild Learning Plan Certificate** — you must earn and download it yourself

## Remaining before zipping
- [ ] Fill in your name and roll number on slide 1 of the PPTX (placeholder: "Add your Name / Roll No.")
- [ ] Choose a licence and commit `LICENSE`
- [ ] `git push` to GitHub and confirm fresh clone works
- [ ] Download IBM SkillsBuild certificate
- [ ] Package → `DocuSense_IBM_SkillsBuild_2026.zip`
