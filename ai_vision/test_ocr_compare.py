"""Compare OCR variants on one photo.

Whole photo:
  python -m ai_vision.test_ocr_compare ml_data/samples/good/photo.jpg
Only a part of the photo (x1 y1 x2 y2 in pixels, e.g. the nutrition table):
  python -m ai_vision.test_ocr_compare ml_data/samples/good/photo.jpg 100 800 700 1500
"""
import sys
import time
from pathlib import Path

import cv2

from ai_vision.image_cleaning import load_image
from ai_vision.ocr_reader import (
    VARIANTS, get_reader, read_ocr_lines, read_ocr_lines_in_box,
)

# So Hindi text does not crash the Windows terminal.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path("ml_data/ocr_preview")


def save_image(path, img):
    ok, buf = cv2.imencode(".jpg", img)
    if ok:
        buf.tofile(str(path))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    path = Path(args[0])
    box = [int(a) for a in args[1:5]] if len(args) == 5 else None

    img = load_image(path)
    if img is None:
        print("Could not read the image:", path)
        return
    print("Photo size:", img.shape[1], "x", img.shape[0])

    print("Loading EasyOCR (first time downloads models)...")
    t0 = time.time()
    get_reader()
    print("Model ready in %.1f s" % (time.time() - t0))

    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    print()
    print("%-9s %6s %10s %12s %8s" % ("variant", "lines", "good(>=.5)", "avg conf", "seconds"))
    print("-" * 52)
    for variant in VARIANTS:
        t = time.time()
        if box:
            lines = read_ocr_lines_in_box(img, box, variant=variant)
        else:
            lines = read_ocr_lines(img, variant=variant)
        secs = time.time() - t
        good = sum(1 for l in lines if l["confidence"] >= 0.5)
        avg = sum(l["confidence"] for l in lines) / len(lines) if lines else 0
        results[variant] = lines
        print("%-9s %6d %10d %12.2f %8.1f" % (variant, len(lines), good, avg, secs))

    best = max(results, key=lambda v: sum(1 for l in results[v] if l["confidence"] >= 0.5))
    lines = results[best]
    print()
    print("Best variant by good lines:", best)
    print("-" * 52)
    for l in lines:
        print("%.2f | %s | %s" % (l["confidence"], l["language"], l["text"]))

    # Save text (UTF-8, Hindi safe) and a picture with boxes.
    stem = path.stem
    text_file = OUT / (stem + "_" + best + ".txt")
    text_file.write_text("\n".join(l["text"] for l in lines), encoding="utf-8")

    drawn = img.copy()
    for l in lines:
        x1, y1, x2, y2 = l["box"]
        color = (0, 160, 0) if l["language"] == "en" else (0, 0, 220)
        cv2.rectangle(drawn, (x1, y1), (x2, y2), color, 2)
    save_image(OUT / (stem + "_" + best + "_boxes.jpg"), drawn)
    print()
    print("Saved text and boxes picture in", OUT)
    print("Green boxes = English, red boxes = Hindi.")


main()