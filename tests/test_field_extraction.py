from src.field_extraction import completeness, extract_fields, to_record
from src.utils import parse_amount, parse_date

TEXT = """Northwind Traders Ltd
INVOICE
Invoice No: INV-2026-001
Invoice Date: 14/03/2026
Due Date: 13/04/2026
Consulting 2 450.00
Subtotal: $1,200.00
Tax (18%): $216.00
Total: $1,416.00
"""


def test_extracts_standard_fields():
    rec = to_record(extract_fields(TEXT))
    assert rec["vendor"] == "Northwind Traders Ltd"
    assert rec["invoice_number"] == "INV-2026-001"
    assert rec["invoice_date"] == "2026-03-14"
    assert rec["due_date"] == "2026-04-13"
    assert (rec["subtotal"], rec["tax"], rec["total"]) == (1200.0, 216.0, 1416.0)
    assert rec["currency"] == "USD"


def test_percent_not_taken_as_tax_amount():
    rec = to_record(extract_fields("Shop\nTax 18% 27.00\nTotal 177.00"))
    assert rec["tax"] == 27.0


def test_grand_total_preferred_over_total_qty():
    rec = to_record(extract_fields("Shop\nTotal Qty 3\nGrand Total 99.50"))
    assert rec["total"] == 99.5


def test_missing_fields_stay_missing_not_guessed():
    ex = extract_fields("random words only\nnothing useful here")
    assert ex["fields"]["total"]["status"] == "missing"
    assert ex["fields"]["invoice_number"]["value"] is None
    assert completeness(ex) < 0.5


def test_empty_text():
    ex = extract_fields("")
    assert all(f["status"] == "missing" for f in ex["fields"].values())


def test_cgst_sgst_summed_and_marked_uncertain():
    ex = extract_fields("Shop\nCGST 9.00\nSGST 9.00\nTotal 118.00")
    assert ex["fields"]["tax"]["value"] == 18.0
    assert ex["fields"]["tax"]["status"] == "uncertain"


def test_gstin_line_not_used_as_tax():
    ex = extract_fields("Shop\nGSTIN 29ABCDE1234F1Z5\nTotal 10.00")
    assert ex["fields"]["tax"]["status"] == "missing"


def test_parse_amount_formats():
    assert parse_amount("1,234.50") == 1234.5
    assert parse_amount("1.234,50") == 1234.5
    assert parse_amount("Rs. 99") == 99.0
    assert parse_amount("(12.00)") == -12.0
    assert parse_amount("abc") is None
    assert parse_amount(None) is None


def test_parse_date_formats():
    assert parse_date("2026-03-14").isoformat() == "2026-03-14"
    assert parse_date("14 Mar 2026").isoformat() == "2026-03-14"
    assert parse_date("March 14, 2026").isoformat() == "2026-03-14"
    assert parse_date("31/02/2026") is None
    assert parse_date("") is None


def test_parse_amount_currency_prefix_and_trailing_dot():
    assert parse_amount("$ 1,200.00") == 1200.0
    assert parse_amount("Rs. 99") == 99.0
    assert parse_amount("12.") == 12.0
