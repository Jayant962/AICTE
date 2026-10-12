import io

import pytest
from PIL import Image

from src.document_loader import DocumentError, load_pages, validate_upload


def png_bytes(size=(50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, "PNG")
    return buf.getvalue()


def test_empty_upload_rejected():
    with pytest.raises(DocumentError):
        validate_upload("a.png", b"")


def test_unsupported_type_rejected():
    with pytest.raises(DocumentError):
        validate_upload("a.exe", b"MZ....")


def test_extension_content_mismatch_rejected():
    with pytest.raises(DocumentError):
        validate_upload("fake.pdf", png_bytes())


def test_oversize_rejected():
    with pytest.raises(DocumentError):
        validate_upload("a.png", png_bytes() + b"0" * 2_000_000, max_mb=1)


def test_valid_png_loads():
    data = png_bytes()
    assert validate_upload("a.PNG", data) == ".png"
    assert len(load_pages(data, ".png")) == 1


def test_corrupted_png_rejected():
    bad = b"\x89PNG\r\n\x1a\n" + b"garbage" * 10
    ext = validate_upload("a.png", bad)
    with pytest.raises(DocumentError):
        load_pages(bad, ext)


def test_corrupted_pdf_rejected():
    bad = b"%PDF-1.4 not really a pdf"
    ext = validate_upload("a.pdf", bad)
    with pytest.raises(DocumentError):
        load_pages(bad, ext)


def test_pdf_pages_load():
    import pymupdf
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "hello")
    doc.new_page()
    pages = load_pages(doc.tobytes(), ".pdf")
    assert len(pages) == 2
