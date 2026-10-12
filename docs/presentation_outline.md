# Final presentation outline (12 slides; PPTX not generated, see ANTIGRAVITY_PROMPT.md)
1. Title: DocuSense, IBM SkillsBuild-AICTE-BharatCares ML & Applied AI Internship 2026 (add your name/ID yourself)
2. Problem: manual invoice errors, duplicates, poor scans
3. Objectives
4. Proposed solution: five separate signals -> human review
5. Architecture diagram (from docs/architecture.md)
6. Dataset: SROIE/CORD candidates, no fraud labels, acquisition status (be explicit if still synthetic-only)
7. Methodology: preprocessing -> OCR -> extraction -> validation
8. OCR and extraction: rule-based, extracted/uncertain/missing, editable fields
9. Validation and duplicate detection: rules, tolerance, exact/near/conflict, threshold trade-off
10. ML component: Isolation Forest, features, contamination, anomaly score != fraud; actual evaluation (only real numbers from reports/)
11. Dashboard screenshots (real captures only; see submission_checklist.md)
12. Limitations and future scope
