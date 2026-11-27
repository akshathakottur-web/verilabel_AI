"""Image quality check for Verilabel AI (Member 2).

Checks three things: resolution, blur, brightness.
All limits are at the top so they are easy to tune.
"""
import cv2

# ---- Limits (tune these after testing on real photos) ----
MIN_SHORT_SIDE = 600       # smaller side of the ORIGINAL photo, in pixels
BLUR_THRESHOLD = 80.0      # Laplacian variance below this = blurry
DARK_THRESHOLD = 60        # average brightness (0-255) below this = too dark
BRIGHT_THRESHOLD = 225     # average brightness above this = too bright
CHECK_SIDE = 1000          # blur is measured at this size so photos compare fairly


def measure(img):
    """Return the raw numbers for one BGR image."""
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    longest = max(h, w)
    if longest != CHECK_SIDE:
        scale = CHECK_SIDE / longest
        gray = cv2.resize(
            gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    return {
        "width": w,
        "height": h,
        "sharpness": round(sharpness, 1),
        "brightness": round(brightness, 1),
    }


def check_quality(img):
    """Return {"image_quality": "ok" or "too_low", "reason": str, "metrics": dict}."""
    m = measure(img)
    problems = []

    if min(m["width"], m["height"]) < MIN_SHORT_SIDE:
        problems.append(
            "Resolution too low (%dx%d)" % (m["width"], m["height"])
        )
    if m["sharpness"] < BLUR_THRESHOLD:
        problems.append("Image is blurry")
    if m["brightness"] < DARK_THRESHOLD:
        problems.append("Image is too dark")
    elif m["brightness"] > BRIGHT_THRESHOLD:
        problems.append("Image is too bright")

    if problems:
        return {
            "image_quality": "too_low",
            "reason": "; ".join(problems),
            "metrics": m,
        }
    return {
        "image_quality": "ok",
        "reason": "Image is clear enough",
        "metrics": m,
    }