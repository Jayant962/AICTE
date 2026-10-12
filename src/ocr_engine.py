"""Tesseract OCR wrapper (requires the Tesseract binary, see README)."""
import os
import shutil

import pytesseract

WINDOWS_DEFAULTS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]


class OCRUnavailableError(RuntimeError):
    pass


def configure_tesseract(cmd=None):
    """Resolve the Tesseract executable: argument > TESSERACT_CMD env > PATH > Windows defaults."""
    candidates = [cmd, os.environ.get("TESSERACT_CMD"), shutil.which("tesseract")] + WINDOWS_DEFAULTS
    for c in candidates:
        if c and os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return c
    return None


def tesseract_available(cmd=None) -> bool:
    configure_tesseract(cmd)
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_image(img, psm=6, lang="eng"):
    """Return (text, mean_word_confidence 0-100 or None)."""
    if not tesseract_available():
        raise OCRUnavailableError(
            "Tesseract OCR not found. Install it and set TESSERACT_CMD (see README)."
        )
    config = f"--oem 3 --psm {psm}"
    data = pytesseract.image_to_data(img, lang=lang, config=config,
                                     output_type=pytesseract.Output.DICT)
    words, confs, lines = [], [], {}
    for i, w in enumerate(data["text"]):
        if not w.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(w)
        try:
            c = float(data["conf"][i])
            if c >= 0:
                confs.append(c)
        except (ValueError, TypeError):
            pass
    text = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
    return text, (sum(confs) / len(confs) if confs else None)


def ocr_images(images, psm=6, lang="eng"):
    texts, confs = [], []
    for img in images:
        t, c = ocr_image(img, psm=psm, lang=lang)
        texts.append(t)
        if c is not None:
            confs.append(c)
    return "\n\n".join(texts), (sum(confs) / len(confs) if confs else None)
