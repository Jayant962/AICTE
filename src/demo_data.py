"""Clearly labelled SYNTHETIC demonstration records (source='synthetic_demo').
They exist only so the dashboard can be demonstrated; they are not real invoices."""
import hashlib

_BASE = [
    ("Northwind Traders Ltd", "INV-2026-001", "2026-03-14", 1200.00, 216.00, 1416.00),
    ("Acme Office Supplies", "AC-77841", "2026-05-02", 86.50, 15.57, 102.07),
    ("Globex Logistics", "GX-5520", "2026-06-20", 500.00, 90.00, 690.00),   # total mismatch
    ("Initech Software", "2026/0415", "2026-04-15", 2500.00, 450.00, 2950.00),
    ("Northwind Traders Limited", "INV-2026-001", "2026-03-14", 1200.00, 216.00, 1416.00),  # duplicate
    ("Acme Office Supplies", "AC-77842", "2026-05-03", 86.50, 15.57, 102.07),  # near-duplicate
    ("Umbrella Services", "UM-3001", "2026-07-01", 300.00, 54.00, 354.00),
    ("Umbrella Services", "UM-3001", "2026-07-02", 300.00, 54.00, 399.00),  # conflict
]


def demo_records():
    out = []
    for v, n, d, s, t, tot in _BASE:
        key = f"synthetic_demo|{v}|{n}|{d}|{tot}"
        out.append({"file_hash": hashlib.sha256(key.encode()).hexdigest(), "file_name": f"demo_{n}",
                    "source": "synthetic_demo", "vendor": v, "invoice_number": n, "invoice_date": d,
                    "subtotal": s, "tax": t, "total": tot, "currency": "USD",
                    "text_excerpt": f"{v}\nINVOICE\nInvoice No: {n}\nInvoice Date: {d}\nSubtotal: {s}\nTax: {t}\nTotal: {tot}"})
    return out
