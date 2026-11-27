"""Make fake bad photos (blurry, dark, small) from good ones, for testing.

Run from the repo root:  python -m ai_vision.make_bad_samples
Reads:  ml_data/samples/good/
Writes: ml_data/samples/blurry/, dark/, small/
"""
from pathlib import Path

import cv2

from ai_vision.image_cleaning import load_image

SAMPLES = Path("ml_data/samples")
GOOD = SAMPLES / "good"
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def save(img, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(folder / (name + ".jpg")), img)


def main():
    files = sorted(p for p in GOOD.glob("*") if p.suffix.lower() in IMAGE_TYPES)
    if not files:
        print("Put some good photos in", GOOD, "first.")
        return

    # Make bad copies from the first 4 good photos.
    for path in files[:4]:
        img = load_image(path)
        if img is None:
            print("Could not read", path.name)
            continue
        stem = path.stem

        blurry = cv2.GaussianBlur(img, (0, 0), 6)
        save(blurry, SAMPLES / "blurry", stem + "_blurry")

        dark = cv2.convertScaleAbs(img, alpha=0.25, beta=0)
        save(dark, SAMPLES / "dark", stem + "_dark")

        h, w = img.shape[:2]
        small = cv2.resize(img, (max(1, w // 8), max(1, h // 8)), interpolation=cv2.INTER_AREA)
        save(small, SAMPLES / "small", stem + "_small")

        print("Made bad copies of", path.name)


main()