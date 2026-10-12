# Lean Canvas: DocuSense (hypotheses only; no market validation performed)

1. **Problem:** Invoices are checked by hand; arithmetic errors, duplicates and unusual amounts are easy to miss.
2. **Customer segments (assumed):** Small finance/accounts-payable teams; students and auditors learning document analysis. *Not validated with real customers.*
3. **Unique value proposition:** Free, local, explainable invoice screening that shows why a record needs review, with no paid APIs.
4. **Solution:** OCR + rule-based extraction, validation engine, fuzzy duplicate detection, optional anomaly detection, review dashboard.
5. **Channels (proposed):** Public GitHub repository, college/internship showcase, demo video.
6. **Revenue streams:** None for the academic prototype. Possible future: hosted version or support (unvalidated idea).
7. **Cost structure:** Developer time; open-source software; local hardware. No paid services.
8. **Key metrics (measured & tracked):**
   - Field-level extraction on CORD v2 real receipts (100 docs): Subtotal precision 87.0% (recall 27.8%), Total precision 46.5% (recall 20.4%), Tax precision 44.4% (recall 8.9%).
   - Validation coverage: 7 deterministic rules covering required fields, date sanity, due-date order, monetary plausibility, total consistency, tax ratio, and invoice number syntax.
   - Anomaly model: Unsupervised Isolation Forest trained on 109 complete records (log_total, tax_ratio) with 5% contamination quantile.
   - Test suite reliability: 51 automated unit/integration tests passing with 100% test success rate.
9. **Unfair advantage:** None claimed; differentiators are transparency, local privacy and zero licence cost.
