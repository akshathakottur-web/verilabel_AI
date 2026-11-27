"""Show whether re-reading a YOLO box (enlarged) beats the whole-photo read.

    python -m ai_vision.debug_crops ml_data/raw_photos/member1/crab_back.png
"""
import sys

from ai_vision import vision_step as vs
from ai_vision.image_cleaning import load_image
from ai_vision.ocr_reader import read_ocr_lines
from ai_vision.yolo_detector import detect_objects

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

img = load_image(sys.argv[1])
if img is None:
    print("Could not read the image.")
    sys.exit(1)

detections = detect_objects(img)
full = read_ocr_lines(img, variant=vs.FULL_PHOTO_VARIANT)

for cls in vs.RE_READ_CLASSES:
    found = [d for d in detections if d["class"] == cls]
    print("=" * 60)
    if not found:
        print(cls, ": not detected")
        continue
    det = max(found, key=lambda d: d["confidence"])
    new, region = vs._reread_crop(img, det["box"])
    if region is None:
        print(cls, ": box too small")
        continue
    old = [l for l in full if vs._center_inside(l["box"], region)]
    old_avg = vs._average_conf(old)
    new_avg = vs._average_conf(new)
    kept = "NEW" if (not old or new_avg >= old_avg) else "OLD"
    print("%s  box=%s  old: %d lines avg %.2f | new: %d lines avg %.2f | kept: %s"
          % (cls, det["box"], len(old), old_avg, len(new), new_avg, kept))
    print("--- OLD (whole-photo read) ---")
    for l in old:
        print("  %.2f  %s" % (l["confidence"], l["text"]))
    print("--- NEW (enlarged crop) ---")
    for l in new:
        print("  %.2f  %s" % (l["confidence"], l["text"]))