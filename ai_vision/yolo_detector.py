"""YOLO detection for Verilabel AI (Member 2).

detect_objects(img) returns a list of:
    {"class": "veg_symbol", "confidence": 0.91, "box": [x1, y1, x2, y2]}
Box is in pixels of the ORIGINAL photo. In Phase 5 this is converted to
the exact shape in contracts/.
The model is loaded ONCE and reused.
"""
from pathlib import Path

MODEL_PATH = Path("ml_data/models/verilabel_yolov8n.pt")

_model = None


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "YOLO model not found at %s. Train it, or get it from the "
                "drive link in the hand-over note." % MODEL_PATH
            )
        from ultralytics import YOLO
        _model = YOLO(str(MODEL_PATH))
    return _model


def detect_objects(img, conf=0.25, imgsz=640):
    """Find the label items in a BGR image."""
    model = get_model()
    result = model.predict(img, imgsz=imgsz, conf=conf, device="cpu", verbose=False)[0]
    detections = []
    for b in result.boxes:
        x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]
        detections.append({
            "class": result.names[int(b.cls[0])],
            "confidence": round(float(b.conf[0]), 3),
            "box": [x1, y1, x2, y2],
        })
    detections.sort(key=lambda d: -d["confidence"])
    return detections