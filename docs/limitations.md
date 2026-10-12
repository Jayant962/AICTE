# Limitations (read before presenting results)

1. **Extraction metrics are limited to CORD v2 receipt data.** CORD is a restaurant-receipt dataset (Indonesian/English). It lacks ground-truth for vendor, invoice number and date fields, so only subtotal, tax and total can be evaluated. Results (subtotal precision 87%, total precision 46.5%) should not be compared to invoice-benchmark papers.
2. **Low recall on financial fields.** Most CORD images produce sparse OCR text (average 133 chars/image). Many amount values are not extracted because Tesseract cannot read small or stylised fonts in the receipt images. High precision where found; low coverage overall.
3. **No anomaly model accuracy claimed.** Isolation Forest is unsupervised and trained on only 109 records with two features (log_total, tax_ratio). It finds statistical outliers in that small distribution, not fraud. No fraud labels exist; no accuracy/precision/recall is reported.
4. **Duplicate detection is heuristic.** Component weights (invoice_number 30%, vendor 20%, amount 25%, date 10%, text 15%) are not statistically validated. No ground-truth duplicate pairs exist; precision/recall is not claimed.
5. **No line-item extraction.** Individual line items (descriptions, unit prices, quantities) are not parsed.
6. **Extraction is rule-based.** Does not handle multi-column layouts, handwriting, rotated text or non-English invoices reliably. No layout-aware model (LayoutLM, Donut) is used.
7. **Ambiguous dates.** Day-first (DD/MM) is assumed for ambiguous numeric dates. A lone `$` symbol is reported as USD but marked uncertain.
8. **SQLite is unencrypted.** Metadata and a 1 500-char text excerpt are stored on local disk without encryption. Not suitable for production or sensitive data.
9. **Alerts are review prompts.** A flagged invoice is **not** proven fraudulent; a human reviewer makes all decisions. DocuSense is not an audit tool.
10. **SROIE not acquired.** Registration at the ICDAR 2019 site is required. The dataset was not downloaded; only CORD v2 was used.
11. ~~Windows execution was not tested.~~ **RESOLVED.** The full pipeline was run on Windows 11 with Python 3.11.9 and Tesseract 5.4.0 (UB-Mannheim). All 51 tests pass.
