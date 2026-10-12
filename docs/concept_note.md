# Concept Note: DocuSense

**Title:** DocuSense - Intelligent Invoice Analysis and Fraud Screening System
**Problem statement:** Manual invoice handling is slow and error-prone; totals may be wrong, fields missing, invoices duplicated, amounts unusual and scans poor.
**Background:** Invoices arrive as PDFs and photos. OCR makes them machine-readable, but text still has to be structured, checked and compared. Public datasets (SROIE, CORD) annotate fields but contain no fraud labels.
**Objectives:** (1) extract vendor, number, dates, subtotal, tax, total, currency; (2) validate arithmetic and dates with configurable tolerance; (3) detect exact, near and conflicting duplicates; (4) add an unsupervised anomaly indicator; (5) present a transparent review view for a human.
**Proposed solution:** A local Streamlit app that keeps OCR results, validation errors, duplicate candidates and anomaly indicators separate and combines them into Low concern / Needs review / High concern with reasons.
**Methodology:** Preprocess (OpenCV) -> OCR (Tesseract / PDF text layer) -> rule-based extraction -> editable correction -> validation rules -> fuzzy duplicate matching against SQLite history -> Isolation Forest on log-total and tax ratio (when >= 100 real records exist) -> screening rules. See `docs/methodology.md`.
**Dataset:** Evaluated on real receipts from **CORD v2** (CC BY 4.0; Naver Clova / Hugging Face). 250 samples acquired; 109 complete records containing subtotal, tax, and total used to train the Isolation Forest anomaly detector (`models/anomaly_model.joblib`). Five synthetic invoices are maintained separately for reproducible test cases and demo walkthroughs.
**Technology stack:** Python 3.11, Streamlit, OpenCV, pytesseract (Tesseract OCR 5.4.0), PyMuPDF, Pillow, Pandas, NumPy, scikit-learn, RapidFuzz, Plotly, Joblib, SQLite, Pytest.
**Expected outcomes & Real Results:** A working prototype that surfaces review-worthy invoices with explanations. Empirical extraction evaluation on 100 CORD v2 documents yielded: subtotal precision 87.0% (recall 27.8%), tax precision 44.4% (recall 8.9%), total precision 46.5% (recall 20.4%). Unsupervised Isolation Forest trained on 109 records (contamination 0.05).
**Limitations:** Rule-based extraction tuned for standard invoice layouts; complex or degraded receipt scans show lower recall. Public datasets lack fraud labels; anomaly detection flags statistical distribution outliers, not confirmed fraud. See `docs/limitations.md`.
**Future scope:** Layout-aware document models (LayoutLM/Donut), token-classification line items, vendor-history profiling, supervised classification if labelled fraud data is acquired, multilingual OCR, authentication and encryption for enterprise deployment.
**References:** see README.
