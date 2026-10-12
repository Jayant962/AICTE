"""Generate SYNTHETIC invoices (images + one PDF) with ground truth, for smoke tests/demos only.
These are NOT real financial documents and must never be reported as benchmark data."""
import csv
import os
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "sample_data")
FONTS = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]

INVOICES = [
    dict(file="synthetic_001.png", vendor="Northwind Traders Ltd", invoice_number="INV-2026-001",
         invoice_date="2026-03-14", due_date="2026-04-13", subtotal=1200.00, tax=216.00, total=1416.00,
         items=[("Consulting services", 2, 450.00), ("Setup fee", 1, 300.00)]),
    dict(file="synthetic_002.png", vendor="Acme Office Supplies", invoice_number="AC-77841",
         invoice_date="2026-05-02", due_date="2026-06-01", subtotal=86.50, tax=15.57, total=102.07,
         items=[("Printer paper", 5, 9.50), ("Toner", 1, 39.00)]),
    dict(file="synthetic_003_mismatch.png", vendor="Globex Logistics", invoice_number="GX-5520",
         invoice_date="2026-06-20", due_date="2026-07-20", subtotal=500.00, tax=90.00, total=690.00,
         items=[("Freight", 1, 500.00)]),  # deliberately wrong total (should be 590.00)
    dict(file="synthetic_004_duplicate_of_001.png", vendor="Northwind Traders Ltd", invoice_number="INV-2026-001",
         invoice_date="2026-03-14", due_date="2026-04-13", subtotal=1200.00, tax=216.00, total=1416.00,
         items=[("Consulting services", 2, 450.00), ("Setup fee", 1, 300.00)]),
    dict(file="synthetic_005.pdf", vendor="Initech Software", invoice_number="2026/0415",
         invoice_date="2026-04-15", due_date="2026-05-15", subtotal=2500.00, tax=450.00, total=2950.00,
         items=[("Annual licence", 1, 2500.00)]),
]


def _font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def render(inv):
    img = Image.new("RGB", (1000, 1300), "white")
    d = ImageDraw.Draw(img)
    big, mid = _font(40), _font(26)
    y = 60
    d.text((60, y), inv["vendor"], fill="black", font=big); y += 80
    d.text((60, y), "INVOICE", fill="black", font=big); y += 80
    for label, key in (("Invoice No:", "invoice_number"), ("Invoice Date:", "invoice_date"), ("Due Date:", "due_date")):
        d.text((60, y), f"{label} {inv[key]}", fill="black", font=mid); y += 44
    y += 30
    d.text((60, y), "Description        Qty     Amount", fill="black", font=mid); y += 44
    for desc, q, amt in inv["items"]:
        d.text((60, y), f"{desc}    {q}    {amt:,.2f}", fill="black", font=mid); y += 44
    y += 40
    d.text((560, y), f"Subtotal: ${inv['subtotal']:,.2f}", fill="black", font=mid); y += 44
    d.text((560, y), f"Tax (18%): ${inv['tax']:,.2f}", fill="black", font=mid); y += 44
    d.text((560, y), f"Total: ${inv['total']:,.2f}", fill="black", font=big)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for inv in INVOICES:
        path = os.path.join(OUT, inv["file"])
        if inv["file"].endswith(".pdf"):
            doc = pymupdf.open()
            page = doc.new_page()
            lines = [inv["vendor"], "INVOICE", f"Invoice No: {inv['invoice_number']}",
                     f"Invoice Date: {inv['invoice_date']}", f"Due Date: {inv['due_date']}", "",
                     f"Subtotal: ${inv['subtotal']:,.2f}", f"Tax (18%): ${inv['tax']:,.2f}",
                     f"Total: ${inv['total']:,.2f}"]
            y = 72
            for ln in lines:
                page.insert_text((72, y), ln, fontsize=14); y += 24
            doc.save(path)
        else:
            render(inv).save(path)
        rows.append({k: inv[k] for k in ("file", "vendor", "invoice_number", "invoice_date", "due_date",
                                         "subtotal", "tax", "total")} | {"synthetic": True})
    with open(os.path.join(OUT, "ground_truth.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} SYNTHETIC invoices to {os.path.abspath(OUT)}")


if __name__ == "__main__":
    sys.exit(main())
