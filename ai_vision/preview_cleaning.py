"""Save the cleaned (denoised) version of one photo so you can look at it.

Run from the repo root:
    python -m ai_vision.preview_cleaning ml_data/samples/good/yourphoto.jpg
"""
import sys
from pathlib import Path

import cv2

from ai_vision.image_cleaning import clean_image, load_image

if len(sys.argv) < 2:
    print("Usage: python -m ai_vision.preview_cleaning path/to/photo.jpg")
    sys.exit(1)

img = load_image(sys.argv[1])
if img is None:
    print("Could not read the image.")
    sys.exit(1)

out = clean_image(img)
folder = Path("ml_data/cleaned_preview")
folder.mkdir(parents=True, exist_ok=True)
stem = Path(sys.argv[1]).stem
cv2.imwrite(str(folder / (stem + "_gray.jpg")), out["gray"])
cv2.imwrite(str(folder / (stem + "_denoised.jpg")), out["denoised"])
print("Saved to", folder)
print("Size after resize:", out["color"].shape[1], "x", out["color"].shape[0])