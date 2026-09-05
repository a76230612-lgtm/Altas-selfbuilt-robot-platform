import argparse
import csv
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224
BATCH = 8
WORKERS = 0
LOW_CONFIDENCE_THRESHOLD = 0.80

PASS_TOP1 = 0.95
PASS_EDGE_AS_SAFE = 0
PASS_SAFE_AS_EDGE = 2


def safe_copy(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        i = 2
        while True:
            candidate = dst_dir / f"{src.stem}_{i}{src.suffix}"
            if not candidate.exists():
                dst = candidate
                break
            i += 1
    shutil.copy2(src, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Full path to ROI best.pt")
    parser.add_argument(
        "--name",
        default="EDGE_ROI_Final_Evaluation",
        help="Output folder name",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    dataset_root = base_dir / "Atlas_Edge_ROI_Dataset"
    val_root = dataset_root / "val"
    edge_dir = val_root / "EDGE"
    safe_dir = val_root / "SAFE"
    output_root = base_dir / args.name

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    print("=" * 82)
    print("Atlas 6.0 - EDGE ROI Model Evaluation")
    print("=" * 82)
    print(f"Model          : {model_path}")
    print(f"Dataset        : {dataset_root}")

    if not model_path.exists():
        print("MODEL CHECK    : FAIL")
        sys.exit(1)

    if not edge_dir.exists() or not safe_dir.exists():
        print("DATASET CHECK  : FAIL")
        sys.exit(2)

    edge_files = sorted(edge_dir.glob("*.jpg"))
    safe_files = sorted(safe_dir.glob("*.jpg"))

    print(f"VAL EDGE       : {len(edge_files)}")
    print(f"VAL SAFE       : {len(safe_files)}")

    if not edge_files or not safe_files:
        print("DATASET CHECK  : FAIL")
        sys.exit(3)

    print("CHECKS         : PASS")
    print()

    model = YOLO(str(model_path))

    metrics = model.val(
        data=str(dataset_root),
        split="val",
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        workers=WORKERS,
        plots=True,
        project=str(output_root),
        name="Ultralytics_Validation",
        exist_ok=True,
        verbose=True,
    )

    top1 = float(metrics.top1)
    top5 = float(metrics.top5)

    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        print(f"CLASS CHECK FAIL: {model.names}")
        sys.exit(4)

    edge_id = name_to_id["EDGE"]
    safe_id = name_to_id["SAFE"]

    folders = {
        "EDGE_as_SAFE": output_root / "EDGE_as_SAFE",
        "SAFE_as_EDGE": output_root / "SAFE_as_EDGE",
        "LOW_CONFIDENCE": output_root / "LOW_CONFIDENCE",
    }

    edge_as_safe = 0
    safe_as_edge = 0
    low_conf = 0
    correct = 0
    rows = []

    items = [("EDGE", p) for p in edge_files] + [("SAFE", p) for p in safe_files]

    print()
    print("Per-image audit...")
    for i, (actual, image_path) in enumerate(items, start=1):
        results = model.predict(
            source=str(image_path),
            imgsz=IMGSZ,
            device=DEVICE,
            verbose=False,
        )
        r = results[0]
        probs = r.probs

        pred_id = int(probs.top1)
        pred = str(r.names[pred_id]).upper()
        conf = float(probs.top1conf)
        edge_prob = float(probs.data[edge_id])
        safe_prob = float(probs.data[safe_id])

        if pred == actual:
            correct += 1
            category = "CORRECT"
        elif actual == "EDGE" and pred == "SAFE":
            edge_as_safe += 1
            category = "EDGE_as_SAFE"
            safe_copy(image_path, folders["EDGE_as_SAFE"])
        elif actual == "SAFE" and pred == "EDGE":
            safe_as_edge += 1
            category = "SAFE_as_EDGE"
            safe_copy(image_path, folders["SAFE_as_EDGE"])
        else:
            category = "OTHER_ERROR"

        if conf < LOW_CONFIDENCE_THRESHOLD:
            low_conf += 1
            safe_copy(image_path, folders["LOW_CONFIDENCE"])

        rows.append({
            "filename": image_path.name,
            "actual": actual,
            "predicted": pred,
            "top1_confidence": f"{conf:.6f}",
            "edge_probability": f"{edge_prob:.6f}",
            "safe_probability": f"{safe_prob:.6f}",
            "category": category,
        })

        print(
            f"[{i:02d}/{len(items)}] actual={actual:<4} "
            f"pred={pred:<4} conf={conf:.3f} "
            f"{'PASS' if pred == actual else 'ERROR'}"
        )

    csv_path = output_root / "edge_roi_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "actual",
                "predicted",
                "top1_confidence",
                "edge_probability",
                "safe_probability",
                "category",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    accuracy = correct / len(rows)
    strict_pass = (
        top1 >= PASS_TOP1
        and edge_as_safe == PASS_EDGE_AS_SAFE
        and safe_as_edge <= PASS_SAFE_AS_EDGE
    )

    print()
    print("=" * 82)
    print("FINAL RESULT")
    print("=" * 82)
    print(f"Top-1 accuracy                : {top1:.4f}")
    print(f"Top-5 accuracy                : {top5:.4f}")
    print(f"Per-image accuracy            : {accuracy:.4f}")
    print(f"EDGE -> SAFE (critical)       : {edge_as_safe}")
    print(f"SAFE -> EDGE (conservative)   : {safe_as_edge}")
    print(f"Low confidence (<0.80)        : {low_conf}")
    print()
    print(f"PASS Top-1                    : >= {PASS_TOP1:.2f}")
    print(f"PASS EDGE -> SAFE             : == {PASS_EDGE_AS_SAFE}")
    print(f"PASS SAFE -> EDGE             : <= {PASS_SAFE_AS_EDGE}")
    print()
    print(f"FINAL RESULT                  : {'PASS' if strict_pass else 'NOT YET PASS'}")
    print(f"Results folder                : {output_root}")
    print("=" * 82)

    sys.exit(0 if strict_pass else 10)


if __name__ == "__main__":
    main()
