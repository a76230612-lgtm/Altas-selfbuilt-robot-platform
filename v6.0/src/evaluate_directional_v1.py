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
LOW_CONFIDENCE = 0.80

PASS_TOP1 = 0.95
PASS_BLOCKED_AS_FREE = 0
PASS_FREE_AS_BLOCKED = 2


def safe_copy(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        i = 2
        while (dst_dir / f"{src.stem}_{i}{src.suffix}").exists():
            i += 1
        dst = dst_dir / f"{src.stem}_{i}{src.suffix}"
    shutil.copy2(src, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--name", default="DIRECTIONAL_V1_Final_Evaluation")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    dataset = base / "Prepared_Atlas_Directional_Dataset"
    free_dir = dataset / "val" / "FREE"
    blocked_dir = dataset / "val" / "BLOCKED"
    out = base / args.name

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        print("MODEL CHECK: FAIL")
        sys.exit(1)

    free_files = sorted(free_dir.glob("*.jpg"))
    blocked_files = sorted(blocked_dir.glob("*.jpg"))
    if not free_files or not blocked_files:
        print("DATASET CHECK: FAIL")
        sys.exit(2)

    model = YOLO(str(model_path))

    metrics = model.val(
        data=str(dataset),
        split="val",
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        workers=WORKERS,
        plots=True,
        project=str(out),
        name="Ultralytics_Validation",
        exist_ok=True,
        verbose=True,
    )

    top1 = float(metrics.top1)

    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}
    if "FREE" not in name_to_id or "BLOCKED" not in name_to_id:
        print(f"CLASS CHECK FAIL: {model.names}")
        sys.exit(3)

    free_id = name_to_id["FREE"]
    blocked_id = name_to_id["BLOCKED"]

    blocked_as_free = 0
    free_as_blocked = 0
    low_conf = 0
    correct = 0
    rows = []

    items = [("BLOCKED", p) for p in blocked_files] + [("FREE", p) for p in free_files]

    for i, (actual, p) in enumerate(items, start=1):
        r = model.predict(source=str(p), imgsz=IMGSZ, device=DEVICE, verbose=False)[0]
        pred_id = int(r.probs.top1)
        pred = str(r.names[pred_id]).upper()
        conf = float(r.probs.top1conf)
        blocked_prob = float(r.probs.data[blocked_id])
        free_prob = float(r.probs.data[free_id])

        if pred == actual:
            correct += 1
            category = "CORRECT"
        elif actual == "BLOCKED" and pred == "FREE":
            blocked_as_free += 1
            category = "BLOCKED_as_FREE"
            safe_copy(p, out / "BLOCKED_as_FREE")
        elif actual == "FREE" and pred == "BLOCKED":
            free_as_blocked += 1
            category = "FREE_as_BLOCKED"
            safe_copy(p, out / "FREE_as_BLOCKED")
        else:
            category = "OTHER_ERROR"

        if conf < LOW_CONFIDENCE:
            low_conf += 1
            safe_copy(p, out / "LOW_CONFIDENCE")

        rows.append({
            "filename": p.name,
            "actual": actual,
            "predicted": pred,
            "top1_confidence": f"{conf:.6f}",
            "blocked_probability": f"{blocked_prob:.6f}",
            "free_probability": f"{free_prob:.6f}",
            "category": category,
        })

        print(
            f"[{i:02d}/{len(items)}] actual={actual:<7} pred={pred:<7} "
            f"conf={conf:.3f} {'PASS' if pred == actual else 'ERROR'}"
        )

    with (out / "directional_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    acc = correct / len(rows)
    passed = (
        top1 >= PASS_TOP1
        and blocked_as_free == PASS_BLOCKED_AS_FREE
        and free_as_blocked <= PASS_FREE_AS_BLOCKED
    )

    print()
    print("=" * 82)
    print("DIRECTIONAL FINAL RESULT")
    print("=" * 82)
    print(f"Top-1 accuracy                  : {top1:.4f}")
    print(f"Per-image accuracy              : {acc:.4f}")
    print(f"BLOCKED -> FREE (critical)      : {blocked_as_free}")
    print(f"FREE -> BLOCKED (conservative)  : {free_as_blocked}")
    print(f"Low confidence (<0.80)          : {low_conf}")
    print()
    print(f"FINAL RESULT                    : {'PASS' if passed else 'NOT YET PASS'}")
    print(f"Results folder                  : {out}")
    print("=" * 82)

    sys.exit(0 if passed else 10)


if __name__ == "__main__":
    main()
