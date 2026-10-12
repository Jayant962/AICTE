from datetime import date

from src.financial_validation import overall_status, validate_invoice

TODAY = date(2026, 10, 11)
GOOD = {"vendor": "A Ltd", "invoice_number": "INV-001", "invoice_date": "2026-03-01",
        "due_date": "2026-03-31", "subtotal": 100.0, "tax": 18.0, "total": 118.0}


def by_rule(results):
    return {r["rule"]: r for r in results}


def test_good_invoice_passes():
    res = validate_invoice(GOOD, today=TODAY)
    assert overall_status(res) == "PASS"


def test_rounding_difference_is_not_failure():
    res = by_rule(validate_invoice({**GOOD, "total": 118.01}, today=TODAY))
    assert res["total_consistency"]["status"] == "PASS"


def test_small_mismatch_is_review_large_is_fail():
    assert by_rule(validate_invoice({**GOOD, "total": 119.5}, today=TODAY))["total_consistency"]["status"] == "REVIEW"
    assert by_rule(validate_invoice({**GOOD, "total": 150.0}, today=TODAY))["total_consistency"]["status"] == "FAIL"


def test_missing_total_fails_missing_vendor_reviews():
    assert by_rule(validate_invoice({**GOOD, "total": None}, today=TODAY))["required_fields"]["status"] == "FAIL"
    assert by_rule(validate_invoice({**GOOD, "vendor": None}, today=TODAY))["required_fields"]["status"] == "REVIEW"


def test_empty_record_does_not_crash():
    res = validate_invoice({}, today=TODAY)
    assert overall_status(res) == "FAIL"


def test_future_date_review_and_unparseable_fail():
    assert by_rule(validate_invoice({**GOOD, "invoice_date": "2027-01-01"}, today=TODAY))["invoice_date_valid"]["status"] == "REVIEW"
    assert by_rule(validate_invoice({**GOOD, "invoice_date": "garbage"}, today=TODAY))["invoice_date_valid"]["status"] == "FAIL"


def test_due_before_invoice_fails():
    assert by_rule(validate_invoice({**GOOD, "due_date": "2026-02-01"}, today=TODAY))["due_date_order"]["status"] == "FAIL"


def test_negative_amount_review():
    assert by_rule(validate_invoice({**GOOD, "total": -118.0}, today=TODAY))["amount_plausibility"]["status"] == "REVIEW"


def test_bad_invoice_number_review():
    assert by_rule(validate_invoice({**GOOD, "invoice_number": "ABC"}, today=TODAY))["invoice_number_format"]["status"] == "REVIEW"


def test_high_tax_ratio_review():
    res = by_rule(validate_invoice({**GOOD, "tax": 80.0, "total": 180.0}, today=TODAY))
    assert res["tax_ratio"]["status"] == "REVIEW"


def test_configurable_tolerance():
    rec = {**GOOD, "total": 118.5}
    assert by_rule(validate_invoice(rec, tol_abs=1.0, today=TODAY))["total_consistency"]["status"] == "PASS"


def test_result_schema():
    for r in validate_invoice(GOOD, today=TODAY):
        assert {"rule", "status", "explanation", "values", "action"} <= r.keys()
