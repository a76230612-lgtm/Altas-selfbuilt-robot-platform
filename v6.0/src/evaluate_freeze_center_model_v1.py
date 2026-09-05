"""
Atlas 6.0 - CENTER Model Evaluator / Threshold Optimizer V1
-----------------------------------------------------------
Evaluates Atlas_Center_Dataset/val and chooses a tri-state threshold:
  BLOCKED if P(BLOCKED) >= T
  FREE    if P(FREE) >= T
  UNKNOWN otherwise

Priority:
  1) BLOCKED -> FREE = 0
  2) FREE -> BLOCKED = 0
  3) UNKNOWN <= 25%
  4) minimize UNKNOWN

If PASS and --freeze is given, creates:
  Atlas_Models/RELEASE_CANDIDATES/atlas_center_release.pt
  Atlas_Models/RELEASE_CANDIDATES/atlas_center_release.json
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO

THRESHOLDS = [round(x / 100, 2) for x in range(50, 96)]
IMGSZ = 224
DEVICE = "cpu"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_images(folder):
    return sorted(folder.glob("*.jpg"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--freeze", action="store_true")
    args = p.parse_args()

    base = Path(__file__).resolve().parent
    model_path = Path(args.model)

    if not model_path.exists():
        print("FAIL: model not found:")
        print(model_path)
        raise SystemExit(1)

    val_root = base / "Atlas_Center_Dataset" / "val"
    blocked_files = collect_images(val_root / "BLOCKED")
    free_files = collect_images(val_root / "FREE")

    print("=" * 88)
    print("Atlas 6.0 - CENTER Model Threshold Evaluation V1")
    print("=" * 88)
    print(f"Model       : {model_path}")
    print(f"VAL BLOCKED : {len(blocked_files)}")
    print(f"VAL FREE    : {len(free_files)}")
    print()

    if not blocked_files or not free_files:
        print("FAIL: validation set must contain both BLOCKED and FREE images.")
        raise SystemExit(2)

    model = YOLO(str(model_path))

    records = []

    for truth, files in [("BLOCKED", blocked_files), ("FREE", free_files)]:
        for img in files:
            r = model.predict(
                source=str(img),
                imgsz=IMGSZ,
                device=DEVICE,
                verbose=False
            )[0]

            names = {int(k): str(v).upper() for k, v in r.names.items()}
            ids = {v: k for k, v in names.items()}

            if "BLOCKED" not in ids or "FREE" not in ids:
                print("FAIL: model classes are not BLOCKED/FREE.")
                print(names)
                raise SystemExit(3)

            bp = float(r.probs.data[ids["BLOCKED"]])
            fp = float(r.probs.data[ids["FREE"]])

            records.append((truth, bp, fp, str(img)))

    print(f"{'THRESH':>7} {'B->F':>7} {'F->B':>7} {'UNKNOWN':>9} {'KNOWN':>7} {'KNOWN_ACC':>10}")

    candidates = []

    for t in THRESHOLDS:
        b_to_f = 0
        f_to_b = 0
        unknown = 0
        known = 0
        known_correct = 0

        for truth, bp, fp, _ in records:
            if bp >= t:
                pred = "BLOCKED"
            elif fp >= t:
                pred = "FREE"
            else:
                pred = "UNKNOWN"

            if pred == "UNKNOWN":
                unknown += 1
                continue

            known += 1

            if pred == truth:
                known_correct += 1
            elif truth == "BLOCKED" and pred == "FREE":
                b_to_f += 1
            elif truth == "FREE" and pred == "BLOCKED":
                f_to_b += 1

        known_acc = known_correct / known if known else 0.0

        print(
            f"{t:7.2f} {b_to_f:7d} {f_to_b:7d} "
            f"{unknown:9d} {known:7d} {known_acc:10.4f}"
        )

        unknown_rate = unknown / len(records)

        if (
            b_to_f == 0 and
            f_to_b == 0 and
            unknown_rate <= 0.25
        ):
            candidates.append(
                (unknown, t, known_acc, b_to_f, f_to_b)
            )

    print()
    if not candidates:
        print("CENTER MODEL RESULT: FAIL")
        print("No threshold satisfies zero cross-class errors with UNKNOWN <= 25%.")
        raise SystemExit(10)

    candidates.sort(key=lambda x: (x[0], x[1]))
    unknown, chosen_t, known_acc, b_to_f, f_to_b = candidates[0]

    print("CENTER MODEL RESULT: PASS")
    print(f"Recommended threshold : {chosen_t:.2f}")
    print(f"BLOCKED -> FREE       : {b_to_f}")
    print(f"FREE -> BLOCKED       : {f_to_b}")
    print(f"UNKNOWN               : {unknown}/{len(records)} ({unknown/len(records):.2%})")
    print(f"Known accuracy        : {known_acc:.4f}")

    if not args.freeze:
        return

    release_dir = base / "Atlas_Models" / "RELEASE_CANDIDATES"
    release_dir.mkdir(parents=True, exist_ok=True)

    out_pt = release_dir / "atlas_center_release.pt"
    out_json = release_dir / "atlas_center_release.json"

    shutil.copy2(model_path, out_pt)

    cfg = {
        "schema": "atlas_center_release_v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_model": str(model_path),
        "sha256": sha256(model_path),
        "imgsz": IMGSZ,
        "threshold": chosen_t,
        "input_geometry": {
            "source": "atlas_directional_release.json",
            "zone": "CENTER"
        },
        "classes": ["BLOCKED", "FREE"],
        "unknown_behavior": "STOP_AND_REOBSERVE",
        "validation": {
            "blocked_count": len(blocked_files),
            "free_count": len(free_files),
            "blocked_to_free": b_to_f,
            "free_to_blocked": f_to_b,
            "unknown": unknown,
            "total": len(records),
            "known_accuracy": known_acc
        }
    }

    out_json.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("CENTER FREEZE RESULT: PASS")
    print(out_pt)
    print(out_json)


if __name__ == "__main__":
    main()
