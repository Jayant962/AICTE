"""Deterministic financial validation rules. Statuses: PASS, REVIEW, FAIL, SKIPPED."""
import re
from datetime import date

from .utils import parse_amount, parse_date

REQUIRED_FIELDS = ("vendor", "invoice_number", "invoice_date", "total")
_ORDER = {"PASS": 0, "SKIPPED": 0, "REVIEW": 1, "FAIL": 2}


def _r(rule, status, explanation, values=None, action=""):
    return {"rule": rule, "status": status, "explanation": explanation,
            "values": values or {}, "action": action}


def validate_invoice(record: dict, tol_abs: float = 0.05, tol_rel: float = 0.005,
                     review_rel: float = 0.02, today: date | None = None) -> list:
    """Run all rules on a flat record. Tolerances are configurable:
    diff <= max(tol_abs, tol_rel*total) -> PASS (rounding);
    diff <= review_rel*total -> REVIEW; else FAIL."""
    today = today or date.today()
    out = []
    subtotal, tax, total = (parse_amount(record.get(k)) for k in ("subtotal", "tax", "total"))
    inv_date, due_date = parse_date(record.get("invoice_date")), parse_date(record.get("due_date"))

    # 1. required fields
    missing = [k for k in REQUIRED_FIELDS if record.get(k) in (None, "")]
    if not missing:
        out.append(_r("required_fields", "PASS", "All required fields are present."))
    else:
        st = "FAIL" if "total" in missing else "REVIEW"
        out.append(_r("required_fields", st, f"Missing required field(s): {', '.join(missing)}.",
                      {"missing": missing}, "Correct the fields manually or check OCR quality."))

    # 2. invoice date
    raw_date = record.get("invoice_date")
    if raw_date in (None, ""):
        out.append(_r("invoice_date_valid", "SKIPPED", "No invoice date available."))
    elif inv_date is None:
        out.append(_r("invoice_date_valid", "FAIL", "Invoice date could not be parsed.",
                      {"invoice_date": raw_date}, "Re-enter the date (YYYY-MM-DD)."))
    elif inv_date > today:
        out.append(_r("invoice_date_valid", "REVIEW", "Invoice date is in the future.",
                      {"invoice_date": inv_date.isoformat()}, "Verify the date (check day/month order)."))
    elif (today - inv_date).days > 365 * 5:
        out.append(_r("invoice_date_valid", "REVIEW", "Invoice date is more than 5 years old.",
                      {"invoice_date": inv_date.isoformat()}, "Verify the date."))
    else:
        out.append(_r("invoice_date_valid", "PASS", "Invoice date is valid.",
                      {"invoice_date": inv_date.isoformat()}))

    # 3. due date
    if record.get("due_date") in (None, ""):
        out.append(_r("due_date_order", "SKIPPED", "No due date available."))
    elif due_date is None:
        out.append(_r("due_date_order", "REVIEW", "Due date could not be parsed.",
                      {"due_date": record.get("due_date")}, "Re-enter the due date."))
    elif inv_date and due_date < inv_date:
        out.append(_r("due_date_order", "FAIL", "Due date is earlier than the invoice date.",
                      {"invoice_date": inv_date.isoformat(), "due_date": due_date.isoformat()},
                      "Check both dates against the document."))
    else:
        out.append(_r("due_date_order", "PASS", "Due date is not before the invoice date."))

    # 4. monetary plausibility
    money = {"subtotal": subtotal, "tax": tax, "total": total}
    present = {k: v for k, v in money.items() if v is not None}
    if not present:
        out.append(_r("amount_plausibility", "SKIPPED", "No monetary values available."))
    else:
        neg = [k for k, v in present.items() if v < 0]
        huge = [k for k, v in present.items() if abs(v) > 1e9]
        if neg:
            out.append(_r("amount_plausibility", "REVIEW",
                          f"Negative value(s): {', '.join(neg)} (could be a credit note).",
                          present, "Confirm whether this is a credit note or an OCR sign error."))
        elif huge:
            out.append(_r("amount_plausibility", "REVIEW", f"Implausibly large value(s): {', '.join(huge)}.",
                          present, "Check for OCR digit errors."))
        elif total is not None and total == 0:
            out.append(_r("amount_plausibility", "REVIEW", "Total is zero.", present, "Verify the total."))
        else:
            out.append(_r("amount_plausibility", "PASS", "Monetary values are non-negative and plausible.", present))

    # 5. subtotal + tax = total
    if total is None or (subtotal is None and tax is None):
        out.append(_r("total_consistency", "SKIPPED",
                      "Needs a total plus a subtotal and/or tax to compare.", money))
    elif subtotal is None:
        out.append(_r("total_consistency", "SKIPPED", "Subtotal missing; cannot verify total.", money,
                      "Enter the subtotal if it appears on the document."))
    else:
        expected = subtotal + (tax or 0.0)
        diff = abs(total - expected)
        tol = max(tol_abs, tol_rel * abs(total))
        vals = {"subtotal": subtotal, "tax": tax, "total": total, "expected_total": round(expected, 2),
                "difference": round(diff, 2), "tolerance": round(tol, 2)}
        if diff <= tol:
            out.append(_r("total_consistency", "PASS", "Subtotal + tax matches total within tolerance.", vals))
        elif diff <= review_rel * abs(total):
            out.append(_r("total_consistency", "REVIEW",
                          "Small mismatch between subtotal + tax and total (could be rounding, discounts, "
                          "shipping or other charges).", vals, "Compare with the original document."))
        else:
            note = " Tax was not extracted, so tax-free was assumed." if tax is None else ""
            out.append(_r("total_consistency", "FAIL",
                          "Subtotal + tax does not match total." + note, vals,
                          "Verify the amounts; consider OCR errors, discounts or additional charges."))

    # 6. tax ratio
    if subtotal and tax is not None and subtotal > 0 and tax >= 0:
        ratio = tax / subtotal
        if ratio > 0.5:
            out.append(_r("tax_ratio", "REVIEW", f"Tax is {ratio:.0%} of subtotal, unusually high.",
                          {"tax_ratio": round(ratio, 4)}, "Check for OCR errors or special taxes."))
        else:
            out.append(_r("tax_ratio", "PASS", f"Tax is {ratio:.1%} of subtotal.", {"tax_ratio": round(ratio, 4)}))
    else:
        out.append(_r("tax_ratio", "SKIPPED", "Subtotal and tax both needed."))

    # 7. invoice-number format
    inv = record.get("invoice_number")
    if inv in (None, ""):
        out.append(_r("invoice_number_format", "SKIPPED", "No invoice number available."))
    else:
        s = str(inv).strip()
        if not re.fullmatch(r"[A-Za-z0-9\-/_.#]{3,30}", s) or not re.search(r"\d", s):
            out.append(_r("invoice_number_format", "REVIEW",
                          "Invoice number has an unusual format (needs 3-30 chars incl. a digit).",
                          {"invoice_number": s}, "Check the number against the document."))
        else:
            out.append(_r("invoice_number_format", "PASS", "Invoice number format looks plausible.",
                          {"invoice_number": s}))
    return out


def overall_status(results: list) -> str:
    worst = max((_ORDER[r["status"]] for r in results), default=0)
    return {0: "PASS", 1: "REVIEW", 2: "FAIL"}[worst]
