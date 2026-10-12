"""Integration tests on SYNTHETIC sample invoices (smoke tests, not benchmarks)."""
import os

import pytest

from src.field_extraction import to_record
from src.ocr_engine import tesseract_available
from src.pipeline import process_document, screen_record

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "sample_data")
needs_samples = pytest.mark.skipif(not os.path.exists(os.path.join(SAMPLES, "synthetic_005.pdf")),
                                   reason="run scripts/make_sample_data.py first")


def _load(name):
    return process_document(name, open(os.path.join(SAMPLES, name), "rb").read())


@needs_samples
def test_digital_pdf_uses_text_layer_and_extracts():
    out = _load("synthetic_005.pdf")
    assert out["text_source"] == "pdf_text_layer"
    assert to_record(out["extraction"])["total"] == 2950.0


@needs_samples
@pytest.mark.skipif(not tesseract_available(), reason="Tesseract not installed")
def test_image_ocr_and_screening_flags_mismatch():
    rec = to_record(_load("synthetic_003_mismatch.png")["extraction"])
    res = screen_record(rec, None, [])
    assert res["validation_status"] == "FAIL"
    assert res["screening"]["category"] == "High concern"


@needs_samples
@pytest.mark.skipif(not tesseract_available(), reason="Tesseract not installed")
def test_duplicate_image_detected_against_history():
    r1 = to_record(_load("synthetic_001.png")["extraction"])
    r4 = to_record(_load("synthetic_004_duplicate_of_001.png")["extraction"])
    history = [{**r1, "id": 1, "file_hash": "other-hash"}]
    res = screen_record({**r4, "file_hash": "new-hash"}, None, history)
    assert res["duplicates"][0]["match_type"] == "exact"
