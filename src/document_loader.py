"""Upload validation and page loading for PDF / JPG / PNG documents."""
import io

import pymupdf
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAGIC = {
    ".pdf": (b"%PDF",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}
MAX_IMAGE_PIXELS = 40_000_000


class DocumentError(Exception):
    """Raised for unsupported, oversized, empty or corrupted uploads."""


def validate_upload(filename: str, data: bytes, max_mb: float = 10.0) -> str:
    """Validate name, size and magic bytes. Returns the lower-case extension."""
    if not data:
        raise DocumentError("The uploaded file is empty.")
    name = (filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentError(
            f"Unsupported file type '{ext or 'none'}'. Allowed: PDF, JPG, JPEG, PNG."
        )
    if len(data) > max_mb * 1024 * 1024:
        raise DocumentError(f"File is larger than the {max_mb:g} MB limit.")
    if not any(data.startswith(m) for m in MAGIC[ext]):
        raise DocumentError(
            "File content does not match its extension (possibly corrupted or renamed)."
        )
    return ext


def load_pages(data: bytes, ext: str, max_pages: int = 5, dpi: int = 200):
    """Return a list of RGB PIL images (one per page, up to max_pages)."""
    if ext == ".pdf":
        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise DocumentError(f"Could not open PDF: {exc}") from exc
        if doc.needs_pass:
            raise DocumentError("PDF is password protected.")
        if doc.page_count == 0:
            raise DocumentError("PDF has no pages.")
        pages = []
        try:
            for i in range(min(doc.page_count, max_pages)):
                pix = doc[i].get_pixmap(dpi=dpi, alpha=False)
                pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        except Exception as exc:
            raise DocumentError(f"Could not render PDF page: {exc}") from exc
        return pages
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        if img.width * img.height > MAX_IMAGE_PIXELS:
            raise DocumentError("Image resolution is too large to process safely.")
        img = ImageOps.exif_transpose(img).convert("RGB")
    except DocumentError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise DocumentError(f"Could not read image (corrupted?): {exc}") from exc
    return [img]


def pdf_text_layer(data: bytes, max_pages: int = 5) -> str:
    """Embedded text of a digital PDF (empty string for scans)."""
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        return "\n".join(doc[i].get_text() for i in range(min(doc.page_count, max_pages))).strip()
    except Exception:
        return ""
