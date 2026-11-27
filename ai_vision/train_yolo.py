"""Train YOLOv8n on the CPU.

Run from the repo root.
Small test (to confirm it works):
    python -m ai_vision.train_yolo --imgsz 320 --epochs 3 --name smoke
Real training:
    python -m ai_vision.train_yolo --imgsz 640 --epochs 60 --name verilabel
The best model is copied to ml_data/models/verilabel_yolov8n.pt
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

MODEL_OUT = Path("ml_data/models/verilabel_yolov8n.pt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml_data/dataset/data_local.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="verilabel")
    args = parser.parse_args()

    model = YOLO("yolov8n.pt")  # small pretrained model, downloaded the first time
    model.train(
        data=args.data,
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        device="cpu",
        workers=0,            # needed on Windows to avoid crashes
        project="ml_data/runs",
        name=args.name,
        exist_ok=True,
        patience=20,          # stop early if it stops improving
    )

    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    if best.exists():
        if args.name == "smoke":
            print("Smoke test finished. Model NOT copied (it is only a test).")
        else:
            MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(best, MODEL_OUT)
            print("Best model copied to", MODEL_OUT)
    else:
        print("Could not find best.pt in", save_dir)


if __name__ == "__main__":
    main()