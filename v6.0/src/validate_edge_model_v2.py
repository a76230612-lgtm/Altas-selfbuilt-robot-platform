from pathlib import Path
import sys

from ultralytics import YOLO


# ============================================================
# Atlas 6.0 - EDGE Model Validation V2
#
# PURPOSE
# - Avoid ambiguous relative output paths.
# - Automatically locate the newest EDGE best.pt.
# - Validate on Prepared_Atlas_Edge_Dataset.
# - Save plots to a deterministic folder beside this script.
# - Print the ACTUAL Ultralytics save_dir.
# - Verify that confusion matrix / prediction images exist.
# ============================================================


DEVICE = "cpu"
IMGSZ = 224
BATCH = 8
WORKERS = 0


def find_latest_edge_model(base_dir: Path):
    candidates = []

    for path in base_dir.rglob("best.pt"):
        p = str(path).lower()

        if "edge" in p:
            candidates.append(path)

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    base_dir = Path(__file__).resolve().parent

    dataset = base_dir / "Prepared_Atlas_Edge_Dataset"

    output_project = base_dir / "Validation_Results"
    output_name = "EDGE_Pilot_V1"

    print()
    print("=" * 78)
    print("Atlas 6.0 - EDGE Model Validation V2")
    print("=" * 78)
    print(f"Working folder : {base_dir}")
    print(f"Dataset        : {dataset}")
    print()

    if not dataset.exists():
        print("DATASET CHECK  : FAIL")
        print("Prepared_Atlas_Edge_Dataset was not found beside this script.")
        sys.exit(1)

    val_safe = dataset / "val" / "SAFE"
    val_edge = dataset / "val" / "EDGE"

    safe_count = len(list(val_safe.glob("*.jpg"))) if val_safe.exists() else 0
    edge_count = len(list(val_edge.glob("*.jpg"))) if val_edge.exists() else 0

    print(f"VAL SAFE count : {safe_count}")
    print(f"VAL EDGE count : {edge_count}")

    if safe_count == 0 or edge_count == 0:
        print("DATASET CHECK  : FAIL")
        print("Both val/SAFE and val/EDGE must contain images.")
        sys.exit(2)

    print("DATASET CHECK  : PASS")
    print()

    model_path = find_latest_edge_model(base_dir)

    if model_path is None:
        print("MODEL CHECK    : FAIL")
        print("No EDGE best.pt was found under the training folder.")
        sys.exit(3)

    print(f"EDGE model     : {model_path}")
    print(f"Model size     : {model_path.stat().st_size} bytes")
    print("MODEL CHECK    : PASS")
    print()

    output_project.mkdir(parents=True, exist_ok=True)

    print("Running Ultralytics classification validation...")
    print()

    model = YOLO(str(model_path))

    metrics = model.val(
        data=str(dataset),
        split="val",
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        workers=WORKERS,
        plots=True,
        project=str(output_project),
        name=output_name,
        exist_ok=True,
        verbose=True,
    )

    save_dir = Path(metrics.save_dir)

    print()
    print("=" * 78)
    print("VALIDATION RESULT")
    print("=" * 78)
    print(f"Actual save_dir : {save_dir}")

    top1 = getattr(metrics, "top1", None)
    top5 = getattr(metrics, "top5", None)

    if top1 is not None:
        print(f"Top-1 accuracy  : {float(top1):.4f}")

    if top5 is not None:
        print(f"Top-5 accuracy  : {float(top5):.4f}")

    expected_files = [
        save_dir / "confusion_matrix.png",
        save_dir / "confusion_matrix_normalized.png",
    ]

    print()
    print("Plot file checks:")

    all_required = True

    for path in expected_files:
        exists = path.exists() and path.stat().st_size > 0
        print(f"  {path.name:<35} : {'PASS' if exists else 'MISSING'}")

        if not exists:
            all_required = False

    pred_files = sorted(save_dir.glob("val_batch*_pred.jpg"))
    label_files = sorted(save_dir.glob("val_batch*_labels.jpg"))

    print(f"  val_batch*_pred.jpg count         : {len(pred_files)}")
    print(f"  val_batch*_labels.jpg count       : {len(label_files)}")

    print()
    print("Files actually present:")

    files = sorted(p for p in save_dir.iterdir() if p.is_file())

    if files:
        for path in files:
            print(f"  {path.name} ({path.stat().st_size} bytes)")
    else:
        print("  NO FILES FOUND")

    print()

    if all_required:
        print("EDGE VALIDATION FILE OUTPUT: PASS")
        print()
        print("Open this exact folder in Windows Explorer:")
        print(save_dir)
        sys.exit(0)

    print("EDGE VALIDATION FILE OUTPUT: CHECK REQUIRED")
    print("The validation ran, but expected plot files are missing.")
    sys.exit(4)


if __name__ == "__main__":
    main()
