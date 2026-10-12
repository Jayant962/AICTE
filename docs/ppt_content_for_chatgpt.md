# DocuSense: In-Depth Project Master Guide & Architecture Context
### Project for IBM SkillsBuild-AICTE-BharatCares (CSRBOX) ML & Applied AI Internship 2026

> **HOW TO USE THIS WITH CHATGPT:**  
> Paste this entire document into ChatGPT and prompt:  
> *"You are an expert AI & Financial Systems Architect. Below is the complete in-depth documentation and technical architecture of my engineering internship project, DocuSense. Based on this comprehensive technical deep-dive, generate a complete, professional, highly detailed presentation (slide deck structure, talking points, visual layouts, and viva defense notes). You have full creative control to organize and select the best slides."*

---

## 1. Executive Summary & Project Background

- **Project Title:** DocuSense: Intelligent Invoice Analysis & Anomaly Screening System
- **Internship Program:** IBM SkillsBuild – AICTE – BharatCares (CSRBOX) Internship 2026
- **Domain:** Applied Machine Learning, Optical Character Recognition (OCR), Rule-based Expert Systems & Financial Auditing
- **Target Persona:** Accounts Payable (AP) departments, financial compliance teams, internal auditors, and small-to-medium enterprises (SMEs) processing high volumes of invoices, receipts, and bills.
- **Core Technology Philosophy:**
  - **100% Free & Open-Source:** Strictly zero reliance on paid commercial APIs (no OpenAI, no Google Cloud Document AI, no AWS Textract).
  - **Explainable & Auditable AI:** No black-box generative hallucinations. Every alert must trace back to explicit mathematical discrepancies, text fuzzy ratios, or statistical isolation bounds.
  - **Human-in-the-Loop Paradigm:** **Alerts are review prompts, NEVER definitive accusations of fraud.** DocuSense assists human auditors; it does not replace financial governance.
  - **Strict Empirical Honesty:** Zero fabricated metrics or synthetic benchmarks masquerading as real. Every reported accuracy, precision, and recall figure originates from verifiable test scripts run against open datasets.

---

## 2. Industry Problem & Business Context

In traditional financial operations and enterprise ERPs:
1. **Manual Data Entry Bottleneck:** Invoice ingestion is labor-intensive, error-prone, and slow. Discrepancies in line items and subtotals are caught late in the payment cycle.
2. **Hidden Inconsistencies & Math Errors:** Invoices with subtle calculation mistakes (subtotal + tax ≠ total, missing discounts, misplaced decimal points) pass through manual glance checks.
3. **Double Billing & Duplicate Invoices:**
   - Vendors accidentally resubmitting an invoice weeks later.
   - Fraudulent resubmissions where the invoice number or date is slightly altered or obfuscated to bypass simple SQL unique-constraint checks (`INV-001` vs `INV-OO1`).
   - "Conflicting invoices" sharing the same invoice number and vendor but demanding different amounts.
4. **Outlier & Anomaly Invisibility:** AP clerks lack quick statistical indicators to know if an invoice is 10× larger than typical historical vendor orders or exhibits an abnormal tax-to-subtotal ratio.
5. **No Consolidated Audit Trail:** Small businesses often lack an integrated system that captures the raw file hash, extracted text, deterministic validation results, duplicate checks, and outlier flags in one verifiable local record.

---

## 3. High-Level System Architecture & 5-Signal Pipeline

DocuSense operates as an automated 5-signal screening pipeline orchestrated in Python:

```
                  [User Upload: PDF / PNG / JPG]
                                 │
                                 ▼
                     Document Validation & Ingestion
                     (SHA-256 Hashing, MIME, Size Check)
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
        Digital PDF Text Layer            Scanned Image / PDF
       (PyMuPDF direct stream)             (Computer Vision Pipeline)
                 │                               │
                 │                        OpenCV Preprocessing
                 │                       (Grayscale, Upscale, Skew)
                 │                               │
                 │                       Tesseract OCR Engine
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                     Field Extraction Engine
          (Keyword-anchored regex + multi-state confidence)
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
     ▼                           ▼                           ▼
Signal 1 & 2:               Signal 3:                   Signal 4:
Completeness &            Fuzzy Duplicate             Unsupervised
Deterministic             Detection Engine         Anomaly Detection
Financial Validation      (RapidFuzz 4 Tiers)      (Isolation Forest)
(7 Business Rules)               │                           │
     │                           │                           │
     └───────────────────────────┼───────────────────────────┘
                                 │
                                 ▼
                    Signal 5: Unified Screening
              (Risk Categorization & Human Explanations)
                                 │
                                 ▼
               Storage, Review UI & Audit Export
          (Local SQLite DB, Streamlit Dashboard, CSV/JSON)
```

---

## 4. Deep-Dive into Core Components & Engineering Implementation

### Module A: Document Loader & Computer Vision Preprocessing
- **Source Files:** `src/document_loader.py`, `src/image_preprocessing.py`
- **Upload Validation:** Enforces MIME validation, file size limits (default 10 MB), and computes an immediate SHA-256 hash of raw bytes for byte-level duplicate recognition.
- **Dual-Path Ingestion:**
  - *Direct Text Layer:* If an uploaded PDF contains digital selectable text (`len(text) > 50` via PyMuPDF/fitz), OCR is bypassed entirely, avoiding OCR degradation and saving compute.
  - *Scanned Document Path:* Non-digital PDFs or raw images (PNG, JPEG) are rendered at high resolution and routed to OpenCV.
- **OpenCV Preprocessing Pipeline:**
  - **Resolution Upscaling:** Resizes small or low-DPI scans to at least 1400 px width to ensure Tesseract has adequate stroke width for character recognition.
  - **Noise Filtering:** Applies Fast Non-Local Means Denoising (`cv2.fastNlMeansDenoising`) or selective median blur for degraded noisy scans.
  - **Projection-Profile Deskewing:** Calculates horizontal projection profiles across an angular sweep of ±10° with 0.5° steps. It maximizes peak variance to detect document skew and rotates the image straight.
  - **Adaptive / Otsu Binarization:** Optional thresholding to separate ink from background textures without eroding fine punctuation marks.

### Module B: OCR Engine
- **Source File:** `src/ocr_engine.py`
- **Engine:** Tesseract 5.4.0 (UB-Mannheim build on Windows / native Linux package).
- **Configuration:** LSTM Neural Network OCR engine (`--oem 3`) running Page Segmentation Mode 6 (`--psm 6`, assumes a single uniform block of text).
- **Confidence Metrics:** Extracts word-level confidence values from Tesseract HOCR/data output, computes an average page-level confidence score (0–100%), and surfaces this to the auditor as a scan quality indicator.
- **Cross-Platform Auto-Discovery:** Automatically inspects standard Linux paths, Windows Program Files, and local user AppData directories (`%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe`), with fallback to environment variables or manual sidebar overrides.

### Module C: Field Extraction Engine (Rule-Based Expert System)
- **Source File:** `src/field_extraction.py`
- **Design Choice:** Rule-based regular expressions anchored on layout patterns rather than LLMs or heavy NLP transformers. This guarantees deterministic behavior, zero inference cost, instant execution, and zero token costs.
- **Fields Extracted:** Vendor Name, Invoice Number, Invoice Date, Due Date, Subtotal, Tax, Total, Currency.
- **Key Extraction Logic:**
  - *Amounts:* Multi-pass regex parsing handling international comma/period decimal formats (`1,250.00` vs `1.250,00`).
  - *OCR Artifact Cleanup:* Custom regex preprocessing specifically handles noisy OCR spacing:
    - `(\d)\s*([.,])\s*(\d) → \1\2\3` (repairs `36 , 300` into `36,300`).
    - `\b(\d{1,3})\s+(\d{3})\b → \1,\2` (repairs space-separated thousands like `259 000` into `259,000`).
  - *Total Anchoring:* Keyword priority heuristics preferring lines matching `grand total`, `total due`, `balance due`, `net payable` over intermediate subtotals.
  - *Dates:* Multi-pattern recognition supporting ISO `YYYY-MM-DD`, slash/dot formats `DD/MM/YYYY`, and written months (`12 Oct 2026`). Defaults to day-first order for ambiguous numerical dates.
  - *Vendor Detection:* Scans upper document lines, filtering out common noise words (`Invoice`, `Receipt`, `Tax`, `Tel`, `GSTIN`).
- **Field-Level Confidence States:**
  - `extracted`: Matched strong keyword-anchored pattern.
  - `uncertain`: Extracted via fallback heuristic (e.g., date found without a preceding "date" keyword, or tax derived from sum of CGST+SGST).
  - `missing`: Field not detected. **Crucially: values are never hallucinated or filled with dummy defaults.**

### Module D: Deterministic Financial Validation Engine
- **Source File:** `src/financial_validation.py`
- **Statuses:** `PASS`, `REVIEW`, `FAIL`, `SKIPPED`.
- **7 Strict Financial Business Rules:**
  1. `required_fields`: Checks presence of Vendor, Invoice Number, Date, and Total. (Missing Total triggers `FAIL`; missing metadata triggers `REVIEW`).
  2. `invoice_date_valid`: Date must parse, must not be in the future, and must not be older than 5 years.
  3. `due_date_order`: Due date must be greater than or equal to the invoice issue date.
  4. `amount_plausibility`: Financial figures must be non-negative and strictly below 1,000,000,000. Catches credit notes and OCR scale errors.
  5. `total_consistency`: Evaluates mathematical integrity:
     $$\text{Expected Total} = \text{Subtotal} + \text{Tax}$$
     - Difference $\le \max(0.05, 0.005 \times \text{Total})$ $\rightarrow$ `PASS` (tolerates minor rounding pennies).
     - Difference $\le 2\% \times \text{Total}$ $\rightarrow$ `REVIEW` (flags potential shipping charges, item discounts, or small OCR slip-ups).
     - Difference $> 2\%$ $\rightarrow$ `FAIL` (severe math discrepancy).
  6. `tax_ratio`: Calculates $\text{Tax} / \text{Subtotal}$. If ratio exceeds $50\%$, triggers `REVIEW` for abnormally high tax rates.
  7. `invoice_number_format`: Checks that invoice string contains 3–30 characters and includes at least one digit.

### Module E: Fuzzy Duplicate Detection Engine
- **Source File:** `src/duplicate_detection.py`
- **Underlying Technology:** RapidFuzz (C++ accelerated Levenshtein string distance).
- **Multi-Tier Duplicate Classification:**
  1. `same_file`: Identical SHA-256 byte hash (exact same physical document uploaded again).
  2. `exact`: Normalised invoice number matches, vendor token ratio $\ge 90\%$, totals match exactly, and dates match.
  3. `conflict`: Same invoice number and same vendor, but amounts or dates differ. This directly catches invoice tampering or conflicting revisions!
  4. `near`: Fuzzy similarity score meets or exceeds threshold (default 85%).
- **Weighted Component Scoring:**
  - Invoice Number Similarity: **30%** (alphanumeric normalisation handles `O` vs `0` OCR noise).
  - Vendor Similarity (`token_sort_ratio`): **20%** (handles word order: "Acme Corp Ltd" vs "Ltd Acme Corp").
  - Amount Proximity ($1 - |\Delta| / \max$): **25%**.
  - Date Match: **10%**.
  - Raw OCR Text Excerpt Similarity: **15%**.

### Module F: Unsupervised Anomaly Detection Engine
- **Source File:** `src/anomaly_detection.py`
- **Algorithm:** Isolation Forest (`sklearn.ensemble.IsolationForest`, 200 estimators, 5% contamination).
- **Feature Engineering:**
  1. $f_1 = \log_{10}(\text{Total} + 1)$: Log-scaled grand total (handles exponential financial scale).
  2. $f_2 = \text{Tax} / (\text{Subtotal} + 10^{-6})$: Continuous tax-to-subtotal ratio.
- **Standardized Pipeline:** Preprocessed through `StandardScaler` inside a scikit-learn `Pipeline` to prevent data leakage and ensure scale invariance.
- **Why Isolation Forest & Why Unsupervised?**
  - In enterprise AP, real verified "fraud" labels are almost non-existent or heavily proprietary. Supervised learning cannot be realistically trained on balanced fraud labels without extreme synthetic bias.
  - Isolation Forest isolates rare anomalies in feature space by recursively partitioning random splits. Points requiring fewer splits have shorter path lengths and receive lower (more negative) anomaly scores.
  - **Viva Note:** Anomaly score indicates statistical deviation from training distribution—**it does NOT represent a probability of fraudulent intent.**

### Module G: Unified Screening & Audit Storage
- **Source Files:** `src/screening.py`, `src/database.py`, `app.py`
- **3 Risk Categories:**
  - 🟢 **Low Concern:** Complete fields, all validation rules pass, zero duplicate triggers, within normal statistical bounds.
  - 🟡 **Needs Review:** Minor issues (missing due date, small tax rounding difference, borderline similarity score, or outlier isolation flag).
  - 🔴 **High Concern:** Calculation failure (math mismatch), conflicting duplicate detected, negative total, or unparseable key data.
- **Audit Logging & Storage:** Zero-configuration SQLite database (`data/DocuSense.db`). Stores metadata, ISO timestamps, text excerpts, validation breakdowns, and user review statuses.
- **Export Capabilities:** One-click CSV and JSON exports enabling downstream ERP integration and archival audits.

---

## 5. Experimental Data & Empirical Evaluation (The Real Numbers)

### Dataset: CORD v2 (Consolidated Receipt Dataset)
- **Origin:** Naver Clova AI research team (released on Hugging Face as `naver-clova-ix/cord-v2`).
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0). Permitted for research and academic prototyping with proper attribution.
- **Composition:** 250 real-world receipt scans (first 250 samples of the train split downloaded via automated script).
- **Usable Subsets:**
  - 100 receipts evaluated for end-to-end extraction accuracy.
  - 109 receipts with complete subtotal, tax, and total records used to train the Isolation Forest.

### Empirical Extraction Performance (From `reports/extraction_eval.json`)

| Field Name | Ground Truth Count | Predicted Count | Correct Matches | Precision | Recall | Explanation for Results |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Subtotal** | 72 | 23 | 20 | **87.0 %** | 27.8 % | High precision; misses occur due to noisy OCR on small receipt fonts. |
| **Tax** | 45 | 9 | 4 | **44.4 %** | 8.9 % | Receipts often fold tax into line items or label it as service charge. |
| **Total** | 98 | 43 | 20 | **46.5 %** | 20.4 % | Many receipt images contain multiple intermediate totals/cash figures. |
| **Vendor** | 0 | 84 | 0 | N/A | N/A | CORD dataset lacks annotated ground-truth vendor labels. |
| **Invoice #** | 0 | 0 | 0 | N/A | N/A | Receipts do not provide standard formal invoice numbers. |
| **Invoice Date**| 0 | 0 | 0 | N/A | N/A | CORD does not provide structured ground-truth date fields. |

### Critical Technical Reflections:
- **Why Precision > Recall?** The regex extraction pipeline is deliberately designed to be conservative: it only extracts an amount when confident in keyword proximity. In financial audits, extracting an incorrect number (false positive) is far more dangerous than failing to extract and deferring to the human reviewer.
- **OCR Character Density:** Across the 100 evaluated CORD samples, Tesseract extracted an average of only 133 characters per image. Noisy receipt scans, thermal printer fading, and low contrast explain the low recall.

---

## 6. Software Engineering Rigor & Verification

- **Automated Test Suite:** **51 comprehensive unit tests** running under `pytest`.
- **Test Coverage Across Modules:**
  - `tests/test_preprocessing.py`: Image resizing, projection deskew angles, thresholding.
  - `tests/test_extraction.py`: Regex extraction, date parsing, comma/dot normalization, missing field behavior.
  - `tests/test_validation.py`: All 7 financial rules, tolerance boundary testing, future date flags.
  - `tests/test_duplicate_detection.py`: Exact matching, `INV-001` vs `INV-OO1` fuzzy matching, conflicting duplicates, weighted scoring.
  - `tests/test_anomaly_detection.py`: Isolation Forest training, pipeline fitting, score boundaries.
  - `tests/test_database.py`: SQLite persistence, schema migration, record filtering.
  - `tests/test_screening.py`: End-to-end signal aggregation and risk category assignment.
- **Environment Verification:** Verified and passing on Windows 11 with Python 3.11.9 and Tesseract 5.4.0.

---

## 7. Limitations, Trade-offs & Viva Defense Guide

### Candid Limitations (Demonstrating Academic Maturity)
1. **Rule-Based Extraction vs LayoutLM:** Rule-based extraction does not learn two-dimensional spatial geometric relationships. Multi-column invoices or unconventional layouts will degrade performance.
2. **Thermal/Noisy Receipts:** Tesseract 5.4 without fine-tuning struggles with low-contrast, crumpled receipts.
3. **No Ground-Truth Fraud Labels:** The anomaly detector flags statistical outliers, not verified fraud. A large genuine order will be flagged for review.
4. **Uncalibrated Heuristics:** Duplicate detection weights (30/20/25/10/15) are intuitive engineering heuristics, not weights optimized via gradient descent on labeled duplicate pairs.
5. **Single-Page / Line-Item Scope:** The prototype extracts document-level summary fields; it does not parse individual line-item tabular grids.

### Future Roadmap
- Integration of multimodal document understanding models (Donut or fine-tuned LayoutLMv3) for token-level classification.
- Line-item table parsing using borderless table detection algorithms.
- Role-based access control (RBAC), TLS encryption, and secure ERP API webhooks for SAP/NetSuite integration.

---

## 8. Suggested Presentation Structure (For ChatGPT to Customize)

When using this context to create slides, typical strong presentation structures include:
- **Slide 1:** Title, Project Scope, Academic Details
- **Slide 2:** The AP Problem: Manual Bottlenecks, Invoicing Errors & Ghost Duplicates
- **Slide 3:** Project Objectives & Engineering Philosophy (Explainable, Free, Human-in-the-Loop)
- **Slide 4:** End-to-End System Architecture & Pipeline Flow
- **Slide 5:** Computer Vision Preprocessing & OCR Engine
- **Slide 6:** Deterministic Financial Validation Engine (The 7 Business Rules)
- **Slide 7:** Multi-Tier Fuzzy Duplicate Detection (RapidFuzz & Conflict Tracking)
- **Slide 8:** Machine Learning Component: Unsupervised Isolation Forest Anomaly Detection
- **Slide 9:** Dataset Profile & Real Empirical Evaluation (CORD v2 Results)
- **Slide 10:** User Interface, Auditing Dashboard & Investigation Workflow
- **Slide 11:** Test Coverage, Verification & Software Quality (51 Passing Unit Tests)
- **Slide 12:** Honest Limitations, Viva Defense Readiness & Future Roadmap
