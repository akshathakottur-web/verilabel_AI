"""Run the vision step on photos in a folder and print one row per photo.

    python -m ai_vision.batch_check ml_data/raw_photos/member2 10
The number at the end is how many photos to check (default 10).
"""
import re
import sys
import time
from pathlib import Path

from ai_vision import analyze_image
from ai_vision.image_cleaning import load_image
from ai_vision.ocr_reader import get_reader

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TYPES = {".jpg", ".jpeg", ".png", ".webp"}
NUTRITION_WORDS = re.compile(r"energy|protein|carbohydrate|total fat|saturated|sugar|sodium|kcal", re.I)
LICENCE = re.compile(r"\d{14}")

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

folder = Path(sys.argv[1])
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
files = sorted(p for p in folder.rglob("*") if p.suffix.lower() in TYPES)[:limit]
if not files:
    print("No photos found in", folder)
    sys.exit(1)

print("Loading models...")
get_reader()

print()
print("%-30s %-10s %-9s %-34s %5s %5s %5s %6s"
      % ("photo", "size", "quality", "detected", "lines", "nutr", "lic", "secs"))
print("-" * 112)
for path in files:
    img = load_image(path)
    size = "%dx%d" % (img.shape[1], img.shape[0]) if img is not None else "unreadable"
    t = time.time()
    result = analyze_image(str(path))
    secs = time.time() - t

    classes = sorted({d["class"] for d in result["detections"]})
    short = ",".join(c.replace("_symbol", "").replace("nutrition_table", "nutr_tbl") for c in classes)
    text = " ".join(l["text"] for l in result["ocr_lines"])
    nutrition_hits = len(NUTRITION_WORDS.findall(text))
    has_licence = "yes" if LICENCE.search(re.sub(r"[\s-]", "", text)) else "no"

    print("%-30s %-10s %-9s %-34s %5d %5d %5s %6.1f" % (
        path.name[-30:], size, result["image_quality"]["status"], short[:34],
        len(result["ocr_lines"]), nutrition_hits, has_licence, secs))

print()
print("nutr = how many nutrition words (energy, protein, fat...) OCR found.")
print("lic  = whether a 14-digit number (licence) was found.")