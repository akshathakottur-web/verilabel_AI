"""Try the trained model on one photo.

Run from the repo root:
    python -m ai_vision.test_yolo ml_data/raw_photos/member2/YOURPHOTO.jpg
"""
import sys
import time
from pathlib import Path

import cv2

from ai_vision.image_cleaning import load_image
from ai_vision.yolo_detector import detect_objects, get_model

OUT = Path("ml_data/yolo_preview")

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

path = Path(sys.argv[1])
img = load_image(path)
if img is None:
    print("Could not read the image:", path)
    sys.exit(1)

get_model()
t = time.time()
detections = detect_objects(img)
print("Detection took %.1f s" % (time.time() - t))

if not detections:
    print("Nothing detected.")
for d in detections:
    print("%.2f  %-16s %s" % (d["confidence"], d["class"], d["box"]))

drawn = img.copy()
for d in detections:
    x1, y1, x2, y2 = d["box"]
    cv2.rectangle(drawn, (x1, y1), (x2, y2), (0, 160, 0), 3)
    cv2.putText(drawn, "%s %.2f" % (d["class"], d["confidence"]), (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 160, 0), 2)

OUT.mkdir(parents=True, exist_ok=True)
ok, buf = cv2.imencode(".jpg", drawn)
if ok:
    buf.tofile(str(OUT / (path.stem + "_detected.jpg")))
print("Saved picture in", OUT)