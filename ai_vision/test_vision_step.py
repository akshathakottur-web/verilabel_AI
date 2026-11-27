"""Run the contract entry point on one photo.

    python -m ai_vision.test_vision_step ml_data/raw_photos/member1/crab_back.png
Saves the result to ml_data/vision_out/<name>.json
"""
import json
import sys
from pathlib import Path

from ai_vision import analyze_image
from ai_vision.ocr_reader import get_reader
from ai_vision.vision_step import run_vision

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

path = Path(sys.argv[1])
print("Loading OCR models (done once)...")
get_reader()

# Same function Member 1 will call:
result = analyze_image(str(path))
# Run again with timings (models are now warm, so this is the real speed):
timings = {}
run_vision(str(path), timings)

q = result["image_quality"]
print("image_quality:", q["status"], "|", repr(q["reason"]))
print("detections:", len(result["detections"]))
for d in result["detections"]:
    print("   %.2f  %-16s %s" % (d["confidence"], d["class"], d["box"]))
print("ocr_lines:", len(result["ocr_lines"]))
for l in result["ocr_lines"][:10]:
    print("   %.2f | %s | %s" % (l["confidence"], l["language"], l["text"]))
if len(result["ocr_lines"]) > 10:
    print("   ... (%d more)" % (len(result["ocr_lines"]) - 10))

print()
print("Time per step on the second run (seconds):")
for key in ("load", "quality", "yolo", "ocr", "total"):
    if key in timings:
        print("   %-8s %.1f" % (key, timings[key]))

out_dir = Path("ml_data/vision_out")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / (path.stem + ".json")
out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print()
print("Saved:", out_file)