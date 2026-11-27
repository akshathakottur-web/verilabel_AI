"""Run the quality check on every image in a folder (and its subfolders)."""
import sys
from pathlib import Path

from ai_vision.image_cleaning import load_image
from ai_vision.quality_check import check_quality

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ai_vision.test_quality ml_data/samples")
        return

    folder = Path(sys.argv[1])
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_TYPES)
    if not files:
        print("No images found in", folder)
        return

    print("%-40s %-8s %9s %10s  %s" % ("file", "quality", "sharpness", "brightness", "reason"))
    print("-" * 110)
    for path in files:
        img = load_image(path)
        name = str(path.relative_to(folder))
        if img is None:
            print("%-40s could not be read" % name)
            continue
        r = check_quality(img)
        m = r["metrics"]
        print(
            "%-40s %-8s %9s %10s  %s"
            % (name[:40], r["image_quality"], m["sharpness"], m["brightness"], r["reason"])
        )


main()