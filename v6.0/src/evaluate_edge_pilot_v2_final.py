from pathlib import Path
import csv
import shutil
import sys

from ultralytics import YOLO

# ============================================================
# Atlas 6.0 - EDGE Pilot V2 Final Acceptance
#
# PURPOSE
# - Validate ONLY EDGE_Pilot_V2.
# - Audit every validation image.
# - Report:
#     Top-1 accuracy
#     EDGE -> SAFE
#     SAFE -> EDGE
#     Low-confidence count (< 0.80)
# - Save confusion matrices and copied error images.
#
# PASS RULE (strict):
#   Top-1 >= 0.95
#   EDGE -> SAFE == 0
#   SAFE -> EDGE <= 2
#
# This script does NOT retrain or modify the dataset.
# ============================================================

DEVICE = "cpu"
IMGSZ = 224
BATCH = 8
WORKERS = 0
LOW_CONFIDENCE_THRESHOLD = 0.80

PASS_TOP1 = 0.95
PASS_EDGE_AS_SAFE = 0
PASS_SAFE_AS_EDGE = 2


def find_v2_model(base_dir: Path):
    candidates = []
    for p in base_dir.rglob("best.pt"):
        low = str(p).lower()
        if "edge_pilot_v2" in low:
            candidates.append(p)

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def safe_copy(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    if dst.exists():
        stem = src.stem
        suffix = src.suffix
        i = 2
        while True:
            candidate = dst_dir / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                dst = candidate
                break
            i += 1

    shutil.copy2(src, dst)


def main():
    base_dir = Path(__file__).resolve().parent
    dataset_root = base_dir / "Prepared_Atlas_Edge_Dataset"
    val_root = dataset_root / "val"
    edge_dir = val_root / "EDGE"
    safe_dir = val_root / "SAFE"

    output_root = base_dir / "EDGE_V2_Final_Acceptance"

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 82)
    print("Atlas 6.0 - EDGE Pilot V2 Final Acceptance")
    print("=" * 82)
    print(f"Working folder : {base_dir}")
    print(f"Dataset        : {dataset_root}")

    if not edge_dir.exists() or not safe_dir.exists():
        print("DATASET CHECK  : FAIL")
        print("Expected Prepared_Atlas_Edge_Dataset\\val\\EDGE and \\SAFE.")
        sys.exit(1)

    edge_files = sorted(edge_dir.glob("*.jpg"))
    safe_files = sorted(safe_dir.glob("*.jpg"))

    print(f"VAL EDGE       : {len(edge_files)}")
    print(f"VAL SAFE       : {len(safe_files)}")

    if not edge_files or not safe_files:
        print("DATASET CHECK  : FAIL")
        print("Validation folders must both contain images.")
        sys.exit(2)

    print("DATASET CHECK  : PASS")

    model_path = find_v2_model(base_dir)

    if model_path is None:
        print("MODEL CHECK    : FAIL")
        print("No best.pt with EDGE_Pilot_V2 in its path was found.")
        sys.exit(3)

    print(f"V2 model       : {model_path}")
    print(f"Model size     : {model_path.stat().st_size} bytes")
    print("MODEL CHECK    : PASS")
    print()

    model = YOLO(str(model_path))

    # Validate with plots
    val_project = output_root / "Ultralytics_Validation"

    print("Running Ultralytics validation...")
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
    save_dir = Path(metrics.save_dir)

    print()
    print(f"Ultralytics save_dir : {save_dir}")
    print(f"Top-1 accuracy       : {top1:.4f}")
    print(f"Top-5 accuracy       : {top5:.4f}")
    print()

    # Audit each image
    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        print("CLASS CHECK    : FAIL")
        print(f"Model classes  : {model.names}")
        sys.exit(4)

    edge_id = name_to_id["EDGE"]
    safe_id = name_to_id["SAFE"]

    audit_dirs = {
        "EDGE_as_SAFE": output_root / "EDGE_as_SAFE",
        "SAFE_as_EDGE": output_root / "SAFE_as_EDGE",
        "LOW_CONFIDENCE": output_root / "LOW_CONFIDENCE",
    }

    rows = []
    edge_as_safe = 0
    safe_as_edge = 0
    low_conf = 0
    correct = 0

    items = [("EDGE", p) for p in edge_files] + [("SAFE", p) for p in safe_files]

    print("Running per-image audit...")
    print()

    for i, (actual, image_path) in enumerate(items, start=1):
        results = model.predict(
            source=str(image_path),
            imgsz=IMGSZ,
            device=DEVICE,
            verbose=False,
        )

        if not results or results[0].probs is None:
            print(f"[{i:02d}/{len(items)}] INFERENCE FAIL {image_path.name}")
            continue

        r = results[0]
        probs = r.probs
        pred_id = int(probs.top1)
        pred = str(r.names[pred_id]).upper()
        conf = float(probs.top1conf)
        edge_prob = float(probs.data[edge_id])
        safe_prob = float(probs.data[safe_id])

        is_correct = pred == actual
        if is_correct:
            correct += 1

        category = "CORRECT"

        if actual == "EDGE" and pred == "SAFE":
            edge_as_safe += 1
            category = "EDGE_as_SAFE"
            safe_copy(image_path, audit_dirs["EDGE_as_SAFE"])

        elif actual == "SAFE" and pred == "EDGE":
            safe_as_edge += 1
            category = "SAFE_as_EDGE"
            safe_copy(image_path, audit_dirs["SAFE_as_EDGE"])

        if conf < LOW_CONFIDENCE_THRESHOLD:
            low_conf += 1
            safe_copy(image_path, audit_dirs["LOW_CONFIDENCE"])

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
            f"[{i:02d}/{len(items)}] "
            f"actual={actual:<4} pred={pred:<4} conf={conf:.3f} "
            f"{'PASS' if is_correct else 'ERROR'}"
        )

    csv_path = output_root / "edge_v2_audit.csv"
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

    audit_accuracy = correct / len(rows) if rows else 0.0

    strict_pass = (
        top1 >= PASS_TOP1
        and edge_as_safe == PASS_EDGE_AS_SAFE
        and safe_as_edge <= PASS_SAFE_AS_EDGE
    )

    summary = [
        "Atlas 6.0 - EDGE Pilot V2 Final Acceptance",
        "=" * 60,
        f"Model: {model_path}",
        f"Validation images: {len(rows)}",
        f"Ultralytics Top-1: {top1:.4f}",
        f"Per-image accuracy: {audit_accuracy:.4f}",
        "",
        f"EDGE -> SAFE (critical): {edge_as_safe}",
        f"SAFE -> EDGE (conservative): {safe_as_edge}",
        f"Low confidence (< {LOW_CONFIDENCE_THRESHOLD:.2f}): {low_conf}",
        "",
        f"Strict pass thresholds:",
        f"Top-1 >= {PASS_TOP1:.2f}",
        f"EDGE -> SAFE == {PASS_EDGE_AS_SAFE}",
        f"SAFE -> EDGE <= {PASS_SAFE_AS_EDGE}",
        "",
        f"FINAL RESULT: {'PASS' if strict_pass else 'NOT YET PASS'}",
    ]

    (output_root / "acceptance_summary.txt").write_text(
        "\n".join(summary),
        encoding="utf-8",
    )

    print()
    print("=" * 82)
    print("FINAL EDGE V2 ACCEPTANCE")
    print("=" * 82)
    print(f"Top-1 accuracy                : {top1:.4f}")
    print(f"EDGE -> SAFE (critical)       : {edge_as_safe}")
    print(f"SAFE -> EDGE (conservative)   : {safe_as_edge}")
    print(f"Low confidence (<0.80)        : {low_conf}")
    print()
    print(f"PASS threshold Top-1          : >= {PASS_TOP1:.2f}")
    print(f"PASS threshold EDGE -> SAFE   : == {PASS_EDGE_AS_SAFE}")
    print(f"PASS threshold SAFE -> EDGE   : <= {PASS_SAFE_AS_EDGE}")
    print()
    print(f"FINAL RESULT                  : {'PASS' if strict_pass else 'NOT YET PASS'}")
    print()
    print(f"Results folder                : {output_root}")
    print(f"Audit CSV                     : {csv_path}")
    print("=" * 82)

    sys.exit(0 if strict_pass else 10)


if __name__ == "__main__":
    main()
