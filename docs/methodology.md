# Methodology

**Preprocessing.** Grayscale, upscale to >=1400 px width, denoise (non-local means, median blur for large images),
deskew by projection-profile search over +/-10 deg. Binarisation is optional (off by default; it can hurt OCR).
**OCR.** Tesseract (`--oem 3 --psm 6`), mean word confidence recorded. Digital PDFs use their embedded text layer.
**Extraction.** Keyword-anchored regular expressions; percentages stripped before amount search; "grand total/amount
due" outranks "total"; CGST+SGST summed and marked `uncertain`; vendor = first prominent top line (`uncertain`).
Missing fields remain missing. Line items are NOT extracted (not implemented).
**Validation.** Seven rules: required fields, date validity, due-date order, amount plausibility, subtotal+tax=total,
tax ratio, invoice-number format. Tolerance: `diff <= max(abs, rel*total)` PASS; `<= 2% of total` REVIEW; else FAIL.
**Duplicates.** Types: same_file (hash), exact, conflict (same number+vendor, other fields differ), near (weighted
RapidFuzz similarity >= threshold). Weights (invoice no. .30, vendor .20, amount .25, date .10, text .15) are heuristic
and unvalidated; unavailable components are excluded and the rest renormalised.
**Anomaly detection.** Features: `log1p(total)`, `tax/subtotal`; only records with total>0, subtotal>0, tax>=0 are
scored. `StandardScaler` + `IsolationForest(200 trees)`; `contamination` is an assumed outlier share that sets the
threshold, not a fraud rate. Minimum 100 training records. Score = `decision_function` (lower = more unusual).
**Screening.** High concern: validation FAIL or exact/same_file/conflict duplicate. Needs review: validation REVIEW,
near-duplicate, anomaly flag, or <75% required fields. Else Low concern. Not a probability.
