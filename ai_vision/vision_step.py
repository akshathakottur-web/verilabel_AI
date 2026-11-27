"""Member 2's vision step.

    from ai_vision.vision_step import run_vision
    result = run_vision("path/to/photo.jpg")

Returns the VISION RESULT exactly as in contracts/PIPELINE_CONTRACT.md:
    image_quality: {"status": "ok" | "too_low", "reason": ""}
    detections:    [{"class", "confidence", "box"}]
    ocr_lines:     [{"text", "confidence", "box", "language"}]
Boxes are [x1, y1, x2, y2] in pixels of the ORIGINAL photo.

Accuracy step: the important boxes found by YOLO are cropped, enlarged and
read again; the new lines replace the old ones in that area when they look
better (higher average confidence).
"""
import time

import cv2

from ai_vision.image_cleaning import load_image
from ai_vision.ocr_reader import read_ocr_lines
from ai_vision.quality_check import check_quality
from ai_vision.yolo_detector import detect_objects

ALLOWED_CLASSES = {
    "veg_symbol", "nonveg_symbol", "nutrition_table",
    "allergen", "fssai_no", "ingredients", "fssai_logo",
}

SKIP_WHEN_LOW_QUALITY = True

# Settings for the accuracy step. Set RE_READ_CLASSES = [] to turn it off.
RE_READ_CLASSES = []
CROP_MARGIN = 12          # pixels added around the YOLO box
CROP_TARGET_WIDTH = 1400  # crops are enlarged towards this width
CROP_MAX_SCALE = 4.0      # never enlarge more than this
FULL_PHOTO_VARIANT = "upscale"


def to_contract(status, reason, detections, ocr_lines):
    """Build the VISION RESULT in the contract's shape."""
    return {
        "image_quality": {
            "status": status,
            "reason": "" if status == "ok" else reason,
        },
        "detections": [
            {
                "class": d["class"],
                "confidence": round(float(d["confidence"]), 3),
                "box": [int(v) for v in d["box"]],
            }
            for d in detections
            if d["class"] in ALLOWED_CLASSES
        ],
        "ocr_lines": [
            {
                "text": l["text"],
                "confidence": round(float(l["confidence"]), 3),
                "box": [int(v) for v in l["box"]],
                "language": l["language"],
            }
            for l in ocr_lines
        ],
    }


def _center_inside(box, region):
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    return region[0] <= cx <= region[2] and region[1] <= cy <= region[3]


def _average_conf(lines):
    if not lines:
        return 0.0
    return sum(l["confidence"] for l in lines) / len(lines)


def _reread_crop(img, box):
    """Crop a box, enlarge it, read it. Returns (lines in original-photo
    pixels, region) or ([], None)."""
    h, w = img.shape[:2]
    x1 = max(0, int(box[0]) - CROP_MARGIN)
    y1 = max(0, int(box[1]) - CROP_MARGIN)
    x2 = min(w, int(box[2]) + CROP_MARGIN)
    y2 = min(h, int(box[3]) + CROP_MARGIN)
    if x2 - x1 < 20 or y2 - y1 < 10:
        return [], None

    crop = img[y1:y2, x1:x2]
    scale = min(CROP_MAX_SCALE, max(1.0, CROP_TARGET_WIDTH / float(x2 - x1)))
    big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    lines = read_ocr_lines(big, variant="clahe")
    for line in lines:
        b = line["box"]
        line["box"] = [int(b[0] / scale) + x1, int(b[1] / scale) + y1,
                       int(b[2] / scale) + x1, int(b[3] / scale) + y1]
    return lines, (x1, y1, x2, y2)


def improve_with_crops(img, detections, ocr_lines):
    """Re-read the important boxes; keep the new lines where they look better."""
    best = {}
    for d in detections:
        if d["class"] in RE_READ_CLASSES:
            if d["class"] not in best or d["confidence"] > best[d["class"]]["confidence"]:
                best[d["class"]] = d

    for cls in RE_READ_CLASSES:
        det = best.get(cls)
        if det is None:
            continue
        new_lines, region = _reread_crop(img, det["box"])
        if not new_lines:
            continue
        old = [l for l in ocr_lines if _center_inside(l["box"], region)]
        if old and _average_conf(new_lines) < _average_conf(old):
            continue    # the first read was better, keep it
        old_ids = set(id(l) for l in old)
        ocr_lines = [l for l in ocr_lines if id(l) not in old_ids] + new_lines

    ocr_lines.sort(key=lambda l: (l["box"][1], l["box"][0]))
    return ocr_lines


def run_vision(image_path, timings=None):
    """Take an image path, return the VISION RESULT (a dict).
    If you pass a dict as `timings`, it is filled with seconds per step."""
    if timings is None:
        timings = {}
    t_start = time.time()

    t = time.time()
    img = load_image(image_path)
    timings["load"] = time.time() - t
    if img is None:
        timings["total"] = time.time() - t_start
        return to_contract("too_low", "Image could not be read", [], [])

    t = time.time()
    quality = check_quality(img)
    timings["quality"] = time.time() - t

    if quality["image_quality"] == "too_low" and SKIP_WHEN_LOW_QUALITY:
        timings["total"] = time.time() - t_start
        return to_contract("too_low", quality["reason"], [], [])

    t = time.time()
    detections = detect_objects(img)
    timings["yolo"] = time.time() - t

    t = time.time()
    ocr_lines = read_ocr_lines(img, variant=FULL_PHOTO_VARIANT)
    timings["ocr"] = time.time() - t

    t = time.time()
    if RE_READ_CLASSES:
        ocr_lines = improve_with_crops(img, detections, ocr_lines)
    timings["ocr_crops"] = time.time() - t

    timings["total"] = time.time() - t_start
    return to_contract(quality["image_quality"], quality["reason"], detections, ocr_lines)