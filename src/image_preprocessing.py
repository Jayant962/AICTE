"""OpenCV preprocessing for OCR. Conservative by default to avoid degrading text."""
import cv2
import numpy as np
from PIL import Image


def _rotate(gray, angle, border=255):
    h, w = gray.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=border)


def estimate_skew_angle(gray, max_angle=10.0, step=0.5):
    """Projection-profile search: the angle maximising row-sum variance."""
    scale = 600.0 / gray.shape[1]
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    binary = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-max_angle, max_angle + step, step):
        score = float(np.var(_rotate(binary, angle, 0).sum(axis=1)))
        if score > best_score:
            best_angle, best_score = float(angle), score
    return best_angle


def preprocess_for_ocr(img: Image.Image, min_width=1400, denoise=True,
                       deskew=True, binarize=False) -> Image.Image:
    """RGB PIL image -> preprocessed grayscale PIL image."""
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    if w < min_width:
        f = min_width / w
        gray = cv2.resize(gray, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    if denoise:
        if gray.shape[0] * gray.shape[1] <= 4_000_000:
            gray = cv2.fastNlMeansDenoising(gray, None, h=8)
        else:
            gray = cv2.medianBlur(gray, 3)
    if deskew:
        angle = estimate_skew_angle(gray)
        if abs(angle) >= 0.5:
            gray = _rotate(gray, angle)
    if binarize:
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 15)
    return Image.fromarray(gray)
