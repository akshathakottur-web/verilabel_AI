"""Member 2 owns this file.

analyze_image(image_path) returns a VISION RESULT exactly as described in
contracts/PIPELINE_CONTRACT.md (image_quality, detections, ocr_lines).

Member 1's pipeline calls this when USE_MOCK_VISION=False.
Models (YOLO, EasyOCR) load once per process on the first call, so the
first scan is slower than the rest.
"""
from ai_vision.vision_step import run_vision


def analyze_image(image_path):
    return run_vision(image_path)