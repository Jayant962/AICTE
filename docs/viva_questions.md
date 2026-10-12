# Viva notes

**OCR vs document understanding?** OCR turns pixels into text; document understanding (LayoutLM, Donut) also uses layout
and learns which text is a total or date. DocuSense uses OCR + rules, which is simpler but less robust.
**Why preprocess?** Upscaling, denoising and deskewing help Tesseract; aggressive thresholding can erase thin strokes, so it is optional.
**Field extraction?** Regexes anchored on keywords (\"total\", \"invoice no\"), amount parsing for 1,234.50 / 1.234,50, date parsing with day-first default. Fields are labelled extracted/uncertain/missing; nothing is guessed.
**Exact vs fuzzy duplicates?** Exact: same normalised number, vendor, total, date. Fuzzy: edit-distance style similarity (RapidFuzz) tolerates OCR errors like O/0. Threshold trade-off: low = more false positives, high = missed near-duplicates.
**Isolation Forest?** Random trees isolate points; anomalies need fewer splits, giving a lower score. `contamination` sets the cut-off quantile.
**Anomaly score vs fraud probability?** The score is a relative \"unusualness\" under the training distribution. Unusual != fraudulent; legitimate large orders score high. No fraud labels, so no probability can be calibrated.
**Train/test leakage?** Duplicate invoices or the same vendor appearing in both train and test inflate scores; split by vendor/document, fit scalers on train only (done inside the Pipeline).
**Evaluation limitations?** Exact-match after normalisation, small samples, synthetic data in this build; no fraud ground truth; validation is rule-based so tests, not accuracy, show reliability.
**Why a human?** Alerts have false positives and negatives and lack business context (credit notes, discounts, new suppliers).

**NEW: What dataset did you evaluate on?** CORD v2 — 250 Indonesian/English restaurant receipts from Hugging Face (`naver-clova-ix/cord-v2`). Licence: CC BY 4.0. Obtained via `pip install datasets` + `python scripts/download_dataset.py --cord-hf 250`.
**NEW: Why is recall so low on financial fields?** Tesseract OCR produces sparse text (average 133 characters) on many CORD images because fonts are small or stylised. When OCR misses text, the regex cannot match — low recall, but high precision when it does find values.
**NEW: How did you fix OCR spacing artifacts?** I added two regex substitutions in `_amounts_in`: `(\d)\s*([.,])\s*(\d) → \1\2\3` to collapse spaces around punctuation (e.g. `36 , 300 → 36,300`), and `\b(\d{1,3})\s+(\d{3})\b → \1,\2` to join space-separated thousands groups (e.g. `259 000 → 259,000`).
**NEW: How does Windows setup differ from Linux?** Tesseract is not in PATH by default on Windows. `src/ocr_engine.py` now includes `%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe` in `WINDOWS_DEFAULTS` so it is found automatically after extracting the UB-Mannheim build. Setting `TESSERACT_CMD` env variable or the sidebar path input are fallbacks.
**NEW: What is the anomaly model trained on?** 109 CORD v2 receipts with complete subtotal, tax and total. Features: `log_total` (log of grand total) and `tax_ratio` (tax ÷ subtotal). Scaler + IsolationForest(200 trees, contamination=0.05) in a sklearn Pipeline. Saved with joblib.
**NEW: Can the duplicate detector handle 'O' vs '0' OCR errors?** Yes. `normalize_invoice_number` strips all non-alphanumeric characters. `fuzz.ratio` on the result gives ≈80% similarity for `INV-2026-001` vs `INV-2026-OO1`, which exceeds the default 85% threshold when other fields also match closely, yielding a `near` match.
**NEW: What licence is CORD v2 under?** CC BY 4.0 — free for research with attribution. Raw data is not committed to the repository (listed in `.gitignore`). The original source and licence are documented in `data/README.md`.

