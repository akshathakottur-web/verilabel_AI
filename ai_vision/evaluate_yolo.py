"""Precision and recall per class.

Run from the repo root:
    python -m ai_vision.evaluate_yolo
"""
import argparse

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="ml_data/models/verilabel_yolov8n.pt")
    parser.add_argument("--data", default="ml_data/dataset/data_local.yaml")
    parser.add_argument("--split", default="val")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    model = YOLO(args.model)
    metrics = model.val(
        data=args.data, split=args.split, imgsz=args.imgsz,
        device="cpu", workers=0, project="ml_data/runs", name="eval", exist_ok=True,
    )

    box = metrics.box
    print()
    print("%-16s %10s %10s %10s" % ("class", "precision", "recall", "mAP50"))
    print("-" * 50)
    for i, class_index in enumerate(box.ap_class_index):
        print("%-16s %10.2f %10.2f %10.2f" % (
            model.names[int(class_index)], box.p[i], box.r[i], box.ap50[i]))
    print("-" * 50)
    print("%-16s %10.2f %10.2f %10.2f" % ("ALL", box.mp, box.mr, box.map50))


if __name__ == "__main__":
    main()