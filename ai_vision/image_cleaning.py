"""Image cleaning for Verilabel AI (Member 2).

Steps: load -> resize -> grayscale -> denoise.
"""
import cv2
import numpy as np

# Photos larger than this (longest side, in pixels) are shrunk.
# Phone photos are often 4000 px wide, which makes OCR slow.
MAX_SIDE = 1600


def load_image(image_path):
    """Read an image file. Returns a BGR image, or None if it cannot be read.

    np.fromfile + imdecode is used because cv2.imread fails on Windows
    paths that contain special characters.
    """
    try:
        data = np.fromfile(str(image_path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def resize_keep_ratio(img, max_side=MAX_SIDE):
    """Shrink the image so its longest side is at most max_side.
    Small images are NOT enlarged here."""
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return img
    scale = max_side / longest
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)


def clean_image(img):
    """Return a dict with three versions of the image:
    color    - resized colour image (BGR)
    gray     - resized grayscale image
    denoised - grayscale image with noise removed
    """
    resized = resize_keep_ratio(img)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(
        gray, None, h=10, templateWindowSize=7, searchWindowSize=21
    )
    return {"color": resized, "gray": gray, "denoised": denoised}