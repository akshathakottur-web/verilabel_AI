"""OCR for Verilabel AI (Member 2).

Two EasyOCR readers (CPU), each loaded ONCE and reused:
  - English-only reader  -> reads English text (most accurate for English)
  - Hindi+English reader -> used only to find real Hindi (Devanagari) lines
Results are merged: where both found text in the same place, the line with
the higher confidence is kept.

Box format used for now: [x_min, y_min, x_max, y_max] in pixels of the
ORIGINAL photo. In Phase 5 this is converted to whatever shape the
contract in contracts/ asks for.
"""
import re

import cv2
import easyocr

from ai_vision.image_cleaning import clean_image

# Ways of preparing the image before OCR. We compare them on real photos.
VARIANTS = ["gray", "clahe", "upscale"]

# Set to False to skip Hindi completely (faster, English only).
USE_HINDI = False

# A Hindi line must be at least this share Devanagari letters, and this confident.
MIN_HINDI_SHARE = 0.6
MIN_HINDI_CONF = 0.4

# Extra EasyOCR settings for readtext(), for tuning. Leave empty at first.
# Examples to try later:  {"mag_ratio": 1.5}   {"text_threshold": 0.6, "low_text": 0.3}
READ_OPTIONS = {}

_en_reader = None
_hi_reader = None
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_LETTERS = re.compile(r"[A-Za-z\u0900-\u097F]")


def get_en_reader():
    """English-only reader. Loaded once."""
    global _en_reader
    if _en_reader is None:
        _en_reader = easyocr.Reader(["en"], gpu=False)
    return _en_reader


def get_hi_reader():
    """Hindi+English reader. Loaded once."""
    global _hi_reader
    if _hi_reader is None:
        _hi_reader = easyocr.Reader(["hi", "en"], gpu=False)
    return _hi_reader


def get_reader():
    """Load all readers now (so the first photo is not slow). Returns the English one."""
    en = get_en_reader()
    if USE_HINDI:
        get_hi_reader()
    return en


def devanagari_share(text):
    """Share of letters in the text that are Devanagari (0.0 to 1.0)."""
    letters = _LETTERS.findall(text)
    if not letters:
        return 0.0
    dev = sum(1 for c in letters if _DEVANAGARI.match(c))
    return dev / len(letters)


def prepare(img, variant):
    """Return the image to give to EasyOCR for this variant."""
    cleaned = clean_image(img)
    gray = cleaned["gray"]
    if variant == "gray":
        return gray
    # CLAHE = boosts local contrast, helps faint or unevenly lit text.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)
    if variant == "clahe":
        return boosted
    if variant == "upscale":
        # Make small text bigger so it is easier to read.
        return cv2.resize(boosted, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    raise ValueError("Unknown variant: " + str(variant))


def _to_lines(raw, sx, sy, language, min_conf):
    """Turn EasyOCR output into our line dicts, boxes mapped to the original photo."""
    lines = []
    for points, text, conf in raw:
        text = text.strip()
        if not text or conf < min_conf:
            continue
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        lines.append({
            "text": text,
            "confidence": round(float(conf), 3),
            "box": [int(min(xs) * sx), int(min(ys) * sy),
                    int(max(xs) * sx), int(max(ys) * sy)],
            "language": language,
        })
    return lines


def _iou(a, b):
    """How much two boxes overlap (0 = none, 1 = identical)."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / float(area_a + area_b - inter)


def _merge(en_lines, hi_lines):
    """Keep all English lines, add real Hindi lines that do not clash with
    a more confident English line."""
    merged = list(en_lines)
    for h in hi_lines:
        if h["confidence"] < MIN_HINDI_CONF:
            continue
        if devanagari_share(h["text"]) < MIN_HINDI_SHARE:
            continue  # mostly Latin letters: that is the English reader's job
        beaten = False
        for e in en_lines:
            if _iou(e["box"], h["box"]) > 0.3 and e["confidence"] >= h["confidence"]:
                beaten = True
                break
        if not beaten:
            # drop English lines that this Hindi line is replacing
            merged = [m for m in merged
                      if not (m["language"] == "en"
                              and _iou(m["box"], h["box"]) > 0.3
                              and m["confidence"] < h["confidence"])]
            h = dict(h)
            h["language"] = "hi"
            merged.append(h)
    return merged


def read_ocr_lines(img, variant="clahe", min_conf=0.2):
    """Read all text in a BGR image. Returns a list of dicts:
    {"text", "confidence", "box": [x1, y1, x2, y2], "language": "en" or "hi"}
    Lines are sorted top to bottom, then left to right.
    """
    work = prepare(img, variant)
    h0, w0 = img.shape[:2]
    h1, w1 = work.shape[:2]
    sx = w0 / w1   # scale to map boxes back to the ORIGINAL photo
    sy = h0 / h1

    en_raw = get_en_reader().readtext(work, **READ_OPTIONS)
    lines = _to_lines(en_raw, sx, sy, "en", min_conf)

    if USE_HINDI:
        hi_raw = get_hi_reader().readtext(work, **READ_OPTIONS)
        hi_lines = _to_lines(hi_raw, sx, sy, "hi", min_conf)
        lines = _merge(lines, hi_lines)

    lines.sort(key=lambda l: (l["box"][1], l["box"][0]))
    return lines


def read_ocr_lines_in_box(img, box, variant="upscale", min_conf=0.2):
    """Read only a part of the photo, e.g. the nutrition table box from YOLO.
    box = [x1, y1, x2, y2] in original-photo pixels.
    Returned boxes are still in original-photo pixels."""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in box]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 - x1 < 10 or y2 - y1 < 10:
        return []
    crop = img[y1:y2, x1:x2]
    lines = read_ocr_lines(crop, variant=variant, min_conf=min_conf)
    for line in lines:
        b = line["box"]
        line["box"] = [b[0] + x1, b[1] + y1, b[2] + x1, b[3] + y1]
    return lines