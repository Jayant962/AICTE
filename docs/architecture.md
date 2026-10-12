# Architecture

```
Upload (PDF/JPG/PNG) -> document_loader (type, size, magic-byte checks; PDF -> pages)
   -> text layer? (digital PDF) --yes--> text
                    \--no--> image_preprocessing (grayscale, upscale, denoise, deskew) -> ocr_engine (Tesseract)
   -> field_extraction (regex/keyword rules; status extracted|uncertain|missing)
   -> user edits values in Streamlit (extracted vs corrected both kept)
   -> financial_validation (PASS/REVIEW/FAIL/SKIPPED)      \
   -> duplicate_detection vs SQLite history                 }-> screening (transparent rules) -> UI / CSV / JSON
   -> feature_engineering -> anomaly_detection (IsolationForest, optional) /
database.py persists metadata + 1,500-char text excerpt (not the file).
```

| Module | Responsibility |
|---|---|
| `src/pipeline.py` | UI-independent orchestration used by `app.py` and scripts |
| `src/screening.py` | Combines indicators into Low concern / Needs review / High concern |
| `app.py` | Four pages: Dashboard, Document processing, Invoice investigation, Model & system evaluation |
| `scripts/` | dataset help, data prep, training, evaluation, synthetic sample generation |

Every indicator (extraction completeness, validation, duplicates, anomaly) stays visible next to the category.
