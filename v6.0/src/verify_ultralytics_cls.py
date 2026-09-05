import argparse
import sys
from pathlib import Path

import torch
import ultralytics
from ultralytics import YOLO

MODEL_FILE = "yolo26n-cls.pt"
IMAGE_SIZE = 224
DEVICE = "cpu"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Full path to one C950 JPG image")
    args = parser.parse_args()

    image_path = Path(args.image).expanduser()

    print("=" * 70)
    print("Atlas 6.0 - Ultralytics Classification Verification")
    print("=" * 70)
    print(f"Python      : {sys.version.split()[0]}")
    print(f"PyTorch     : {torch.__version__}")
    print(f"Ultralytics : {ultralytics.__version__}")
    print(f"Device      : {DEVICE}")
    print(f"Image       : {image_path}")

    if not image_path.exists() or not image_path.is_file():
        print("IMAGE CHECK : FAIL")
        sys.exit(1)

    print(f"IMAGE CHECK : PASS ({image_path.stat().st_size} bytes)")

    try:
        model = YOLO(MODEL_FILE)
    except Exception as exc:
        print("MODEL LOAD  : FAIL")
        print(exc)
        sys.exit(2)

    print("MODEL LOAD  : PASS")

    try:
        results = model.predict(
            source=str(image_path),
            imgsz=IMAGE_SIZE,
            device=DEVICE,
            verbose=False,
        )
    except Exception as exc:
        print("INFERENCE   : FAIL")
        print(exc)
        sys.exit(3)

    if not results or results[0].probs is None:
        print("INFERENCE   : FAIL")
        sys.exit(4)

    result = results[0]

    print("Top-5 PRETRAINED classification results")
    print("-" * 60)

    for rank, (class_id, confidence) in enumerate(
        zip(result.probs.top5, result.probs.top5conf),
        start=1,
    ):
        class_id = int(class_id)
        confidence = float(confidence)
        print(f"{rank}. {result.names[class_id]:<30} {confidence:.4f}")

    print("-" * 60)
    print("INFERENCE TEST: PASS")
    print("These are generic pretrained labels, not FREE/BLOCKED/EDGE yet.")


if __name__ == "__main__":
    main()
