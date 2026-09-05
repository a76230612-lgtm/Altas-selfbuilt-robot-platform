from pathlib import Path
import csv
import shutil
import sys

from ultralytics import YOLO


# ============================================================
# Atlas 6.0 - EDGE Model Error Audit V1
#
# PURPOSE
# - Use the current EDGE best.pt.
# - Run inference on every validation image.
# - Separate the two critical error types:
#
#     Actual EDGE -> Predicted SAFE   (dangerous false negative)
#     Actual SAFE -> Predicted EDGE   (conservative false positive)
#
# - Export:
#     edge_validation_audit.csv
#     EDGE_as_SAFE/
#     SAFE_as_EDGE/
#     CORRECT_EDGE/
#     CORRECT_SAFE/
#     LOW_CONFIDENCE/
#     audit_summary.txt
#
# IMPORTANT
# - This script does NOT retrain the model.
# - It does NOT change the dataset.
# - It only audits the current validation result.
# ============================================================


DEVICE = "cpu"
IMGSZ = 224
LOW_CONFIDENCE_THRESHOLD = 0.80


def find_latest_edge_model(base_dir: Path):
    candidates = []

    for path in base_dir.rglob("best.pt"):
        low = str(path).lower()

        # Prefer real training outputs, not audit/validation copies.
        if "edge" in low and "validation_results" not in low:
            candidates.append(path)

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def safe_copy(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    # Avoid accidental overwrite if same name exists.
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
    return dst


def main():
    base_dir = Path(__file__).resolve().parent
    dataset_root = base_dir / "Prepared_Atlas_Edge_Dataset"
    val_root = dataset_root / "val"

    actual_edge_dir = val_root / "EDGE"
    actual_safe_dir = val_root / "SAFE"

    audit_root = base_dir / "EDGE_Error_Audit_V1"

    if audit_root.exists():
        shutil.rmtree(audit_root)

    audit_root.mkdir(parents=True, exist_ok=True)

    folders = {
        "EDGE_as_SAFE": audit_root / "EDGE_as_SAFE",
        "SAFE_as_EDGE": audit_root / "SAFE_as_EDGE",
        "CORRECT_EDGE": audit_root / "CORRECT_EDGE",
        "CORRECT_SAFE": audit_root / "CORRECT_SAFE",
        "LOW_CONFIDENCE": audit_root / "LOW_CONFIDENCE",
    }

    print()
    print("=" * 80)
    print("Atlas 6.0 - EDGE Model Error Audit V1")
    print("=" * 80)
    print(f"Working folder : {base_dir}")
    print(f"Validation set : {val_root}")
    print()

    if not actual_edge_dir.exists() or not actual_safe_dir.exists():
        print("DATASET CHECK: FAIL")
        print("Expected val/EDGE and val/SAFE folders were not found.")
        sys.exit(1)

    edge_files = sorted(actual_edge_dir.glob("*.jpg"))
    safe_files = sorted(actual_safe_dir.glob("*.jpg"))
    all_items = [("EDGE", p) for p in edge_files] + [("SAFE", p) for p in safe_files]

    print(f"Actual EDGE images : {len(edge_files)}")
    print(f"Actual SAFE images : {len(safe_files)}")
    print(f"Total val images   : {len(all_items)}")

    if not all_items:
        print("DATASET CHECK: FAIL - no validation images.")
        sys.exit(2)

    model_path = find_latest_edge_model(base_dir)

    if model_path is None:
        print("MODEL CHECK: FAIL - no EDGE best.pt found.")
        sys.exit(3)

    print()
    print(f"EDGE model         : {model_path}")
    print("MODEL CHECK        : PASS")
    print()

    model = YOLO(str(model_path))

    # Determine class IDs from model names instead of assuming ordering.
    name_to_id = {str(name).upper(): int(idx) for idx, name in model.names.items()}

    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        print("CLASS CHECK: FAIL")
        print(f"Model classes: {model.names}")
        sys.exit(4)

    edge_id = name_to_id["EDGE"]
    safe_id = name_to_id["SAFE"]

    print(f"Model class mapping : EDGE={edge_id}, SAFE={safe_id}")
    print()

    csv_path = audit_root / "edge_validation_audit.csv"

    rows = []

    correct = 0
    edge_as_safe = 0
    safe_as_edge = 0
    correct_edge = 0
    correct_safe = 0
    low_confidence = 0

    for index, (actual_label, image_path) in enumerate(all_items, start=1):
        results = model.predict(
            source=str(image_path),
            imgsz=IMGSZ,
            device=DEVICE,
            verbose=False,
        )

        if not results or results[0].probs is None:
            print(f"[{index}/{len(all_items)}] INFERENCE FAIL: {image_path.name}")
            continue

        result = results[0]
        probs = result.probs

        predicted_id = int(probs.top1)
        predicted_label = str(result.names[predicted_id]).upper()
        top1_conf = float(probs.top1conf)

        data = probs.data
        edge_prob = float(data[edge_id])
        safe_prob = float(data[safe_id])

        is_correct = predicted_label == actual_label

        if is_correct:
            correct += 1

            if actual_label == "EDGE":
                correct_edge += 1
                category = "CORRECT_EDGE"
            else:
                correct_safe += 1
                category = "CORRECT_SAFE"

        else:
            if actual_label == "EDGE" and predicted_label == "SAFE":
                edge_as_safe += 1
                category = "EDGE_as_SAFE"

            elif actual_label == "SAFE" and predicted_label == "EDGE":
                safe_as_edge += 1
                category = "SAFE_as_EDGE"

            else:
                category = "OTHER_ERROR"

        if category in folders:
            safe_copy(image_path, folders[category])

        if top1_conf < LOW_CONFIDENCE_THRESHOLD:
            low_confidence += 1
            safe_copy(image_path, folders["LOW_CONFIDENCE"])

        rows.append({
            "filename": image_path.name,
            "actual": actual_label,
            "predicted": predicted_label,
            "correct": is_correct,
            "top1_confidence": f"{top1_conf:.6f}",
            "edge_probability": f"{edge_prob:.6f}",
            "safe_probability": f"{safe_prob:.6f}",
            "category": category,
        })

        print(
            f"[{index:02d}/{len(all_items)}] "
            f"actual={actual_label:<4} "
            f"pred={predicted_label:<4} "
            f"conf={top1_conf:.3f} "
            f"{'PASS' if is_correct else 'ERROR'}"
        )

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "actual",
                "predicted",
                "correct",
                "top1_confidence",
                "edge_probability",
                "safe_probability",
                "category",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    accuracy = correct / total if total else 0.0

    summary_lines = [
        "Atlas 6.0 - EDGE Model Error Audit V1",
        "=" * 60,
        f"Model: {model_path}",
        f"Total validation images: {total}",
        f"Correct: {correct}",
        f"Accuracy: {accuracy:.4f}",
        "",
        f"Actual EDGE -> Predicted SAFE : {edge_as_safe}",
        f"Actual SAFE -> Predicted EDGE : {safe_as_edge}",
        "",
        f"Correct EDGE: {correct_edge}",
        f"Correct SAFE: {correct_safe}",
        f"Low confidence (< {LOW_CONFIDENCE_THRESHOLD:.2f}): {low_confidence}",
        "",
        f"Audit folder: {audit_root}",
        f"CSV: {csv_path}",
    ]

    summary_path = audit_root / "audit_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print()
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total                         : {total}")
    print(f"Correct                       : {correct}")
    print(f"Accuracy                      : {accuracy:.4f}")
    print()
    print(f"EDGE -> SAFE (critical)       : {edge_as_safe}")
    print(f"SAFE -> EDGE (conservative)   : {safe_as_edge}")
    print(f"Low confidence (<0.80)        : {low_confidence}")
    print()
    print(f"Audit folder                  : {audit_root}")
    print(f"CSV                           : {csv_path}")
    print()
    print("ERROR AUDIT: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
