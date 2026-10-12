from src.duplicate_detection import find_duplicates

BASE = {"id": 1, "vendor": "Northwind Traders Ltd", "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-14", "total": 1416.0, "file_hash": "h1", "text_excerpt": ""}


def new(**kw):
    return {"id": None, "file_hash": "h2", **{k: v for k, v in BASE.items() if k not in ("id", "file_hash")}, **kw}


def types(matches):
    return [m["match_type"] for m in matches]


def test_exact_duplicate_with_formatting_differences():
    m = find_duplicates(new(vendor="NORTHWIND TRADERS LIMITED", invoice_number="inv 2026 001"), [BASE])
    assert types(m) == ["exact"]


def test_same_file_hash():
    assert types(find_duplicates({**new(), "file_hash": "h1"}, [BASE]))[0] == "same_file"


def test_conflict_same_number_different_total():
    m = find_duplicates(new(total=1999.0), [BASE])
    assert types(m) == ["conflict"]
    assert "total differs" in m[0]["reasons"][0]


def test_near_duplicate_ocr_error_in_number():
    m = find_duplicates(new(invoice_number="INV-2026-OO1"), [BASE], threshold=80)
    assert types(m) == ["near"]


def test_similar_but_different_invoice_not_flagged():
    other = new(vendor="Different Co", invoice_number="ZZ-9", invoice_date="2025-01-01", total=50.0)
    assert find_duplicates(other, [BASE]) == []


def test_threshold_controls_near_matches():
    rec = new(invoice_number="INV-2026-002", total=1416.0, invoice_date="2026-03-15")
    assert find_duplicates(rec, [BASE], threshold=99) == []
    assert types(find_duplicates(rec, [BASE], threshold=70)) == ["near"]


def test_empty_history_and_self_exclusion():
    assert find_duplicates(new(), []) == []
    assert find_duplicates(BASE, [BASE]) == []


def test_missing_fields_do_not_crash():
    assert find_duplicates({"id": None}, [BASE]) == []


def test_amount_rounding_in_duplicate():
    # Amounts within 0.01 (e.g., float precision or rounding) should have 100% amount similarity
    rec = new(total=1416.008)
    matches = find_duplicates(rec, [BASE])
    assert len(matches) > 0
    assert matches[0]["components"]["amount"] == 100.0


def test_vendor_suffix_variants_in_duplicate():
    # Different legal suffixes (Ltd vs Inc vs Corporation) normalize out
    rec = new(vendor="Northwind Traders Inc")
    matches = find_duplicates(rec, [BASE])
    assert len(matches) > 0
    assert matches[0]["components"]["vendor"] == 100.0

