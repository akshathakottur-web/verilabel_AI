"""Train YOLOv8n on the CPU.

Run from the repo root.
Small test (to confirm it works):
    python -m ai_vision.train_yolo --imgsz 320 --epochs 3 --name smoke
Real training from scratch:
    python -m ai_vision.train_yolo --imgsz 640 --epochs 100 --name verilabel
Continue from an earlier model:
    python -m ai_vision.train_yolo --weights ml_data/models/verilabel_yolov8n.pt --epochs 80 --name verilabel2 --out ml_data/models/verilabel_v2.pt
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

RUNS_DIR = Path("ml_data/runs").resolve()   # absolute, so Ultralytics keeps it as is


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml_data/dataset/data_local.yaml")
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--patience", type=int, default=50)
    parser.add_argument("--name", default="verilabel")
    parser.add_argument("--out", default="ml_data/models/verilabel_yolov8n.pt")
    args = parser.parse_args()

    model = YOLO(args.weights)
    model.train(
        data=args.data,
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        device="cpu",
        workers=0,            # needed on Windows to avoid crashes
        project=str(RUNS_DIR),
        name=args.name,
        exist_ok=True,
        patience=args.patience,   # stop early only after this many epochs without improvement
    )

    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    print("Training output folder:", save_dir)
    if best.exists():
        if args.name == "smoke":
            print("Smoke test finished. Model NOT copied (it is only a test).")
        else:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(best, out)
            print("Best model copied to", out)
    else:
        print("Could not find best.pt in", save_dir)


if __name__ == "__main__":
    main()