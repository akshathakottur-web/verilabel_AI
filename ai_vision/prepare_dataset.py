"""Fix the dataset paths and print counts.

Run from the repo root:  python -m ai_vision.prepare_dataset
Reads:  ml_data/dataset/data.yaml  (from Roboflow)
Writes: ml_data/dataset/data_local.yaml  (used for training)
"""
from collections import Counter
from pathlib import Path

import yaml

DATASET = Path("ml_data/dataset")


def count_split(split_dir):
    images_dir = DATASET / split_dir / "images"
    labels_dir = DATASET / split_dir / "labels"
    images = [p for p in images_dir.glob("*") if p.is_file()] if images_dir.exists() else []
    boxes = Counter()
    if labels_dir.exists():
        for label_file in labels_dir.glob("*.txt"):
            for line in label_file.read_text().splitlines():
                parts = line.split()
                if parts:
                    boxes[int(parts[0])] += 1
    return len(images), boxes


def main():
    src = DATASET / "data.yaml"
    if not src.exists():
        print("Cannot find", src, "- unzip the Roboflow export into ml_data/dataset first.")
        return

    cfg = yaml.safe_load(src.read_text())
    names = cfg["names"]
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names)]
    print("Classes in Roboflow order:", names)

    expected = {"fssai_logo", "veg_symbol", "nonveg_symbol", "nutrition_table"}
    if set(names) != expected:
        print("WARNING: class names are not the 4 expected ones:", sorted(expected))

    val_dir = "valid" if (DATASET / "valid").exists() else "val"
    lines = [
        "path: " + DATASET.resolve().as_posix(),
        "train: train/images",
        "val: %s/images" % val_dir,
        "names:",
    ]
    for i, n in enumerate(names):
        lines.append("  %d: %s" % (i, n))
    out = DATASET / "data_local.yaml"
    out.write_text("\n".join(lines) + "\n")
    print("Wrote", out)

    for split in ("train", val_dir):
        n_img, boxes = count_split(split)
        print()
        print("%s: %d images" % (split, n_img))
        for i, n in enumerate(names):
            print("   %-16s %d boxes" % (n, boxes.get(i, 0)))


main()