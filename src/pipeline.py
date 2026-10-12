"""End-to-end document processing and screening (UI-independent)."""
from . import database
from .anomaly_detection import predict_record
from .document_loader import load_pages, pdf_text_layer, validate_upload
from .duplicate_detection import find_duplicates
from .field_extraction import completeness, extract_fields, to_record
from .financial_validation import overall_status, validate_invoice
from .image_preprocessing import preprocess_for_ocr
from .ocr_engine import ocr_images
from .screening import screen
from .utils import sha256_bytes


def process_document(filename: str, data: bytes, max_mb=10.0, psm=6, binarize=False):
    """Validate -> load -> (text layer | preprocess+OCR) -> extract. Returns a dict."""
    ext = validate_upload(filename, data, max_mb=max_mb)
    pages = load_pages(data, ext)
    text, conf, source = "", None, "ocr"
    if ext == ".pdf":
        text = pdf_text_layer(data)
        if len(text) > 50:
            source = "pdf_text_layer"
    if source == "ocr":
        prepped = [preprocess_for_ocr(p, binarize=binarize) for p in pages]
        text, conf = ocr_images(prepped, psm=psm)
    extraction = extract_fields(text)
    return {"file_name": filename, "file_hash": sha256_bytes(data), "ext": ext, "pages": pages,
            "text_source": source, "ocr_confidence": conf, "extraction": extraction}


def screen_record(record: dict, extraction: dict, history: list, tol_abs=0.05, tol_rel=0.005,
                  dup_threshold=85.0, model_path=None, today=None):
    """Validate, find duplicates, score anomaly and combine. `record` = flat (possibly user-corrected) values."""
    validation = validate_invoice(record, tol_abs=tol_abs, tol_rel=tol_rel, today=today)
    dups = find_duplicates(record, history, threshold=dup_threshold)
    kwargs = {"path": model_path} if model_path else {}
    anomaly = predict_record(record, **kwargs)
    comp = completeness({"fields": {k: {"status": "missing" if record.get(k) in (None, "") else "extracted"}
                                    for k in ("vendor", "invoice_number", "invoice_date", "total")}})
    result = screen(comp, validation, dups, anomaly)
    return {"validation": validation, "validation_status": overall_status(validation),
            "duplicates": dups, "anomaly": anomaly, "completeness": comp, "screening": result}


def to_db_record(base: dict, record: dict, file_hash: str, file_name: str, text: str,
                 screening_result: dict, user_corrected: bool, source="upload") -> dict:
    return {**record, "file_hash": file_hash, "file_name": file_name, "source": source,
            "text_excerpt": text, "completeness": screening_result["completeness"],
            "user_corrected": user_corrected, "validation": screening_result["validation"],
            "validation_status": screening_result["validation_status"],
            "duplicates": [{k: v for k, v in d.items() if k != "other"} | {"other_id": d["other"].get("id")}
                           for d in screening_result["duplicates"]],
            "anomaly": screening_result["anomaly"],
            "screening_category": screening_result["screening"]["category"],
            "indicators": screening_result["screening"]["indicators"]}
