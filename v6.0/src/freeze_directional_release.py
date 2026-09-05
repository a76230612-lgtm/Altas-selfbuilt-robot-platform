import argparse
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
MAX_UNKNOWN_RATIO = 0.25


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Full path to passed Directional best.pt")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    val_root = base / "Prepared_Atlas_Directional_Dataset" / "val"
    blocked_dir = val_root / "BLOCKED"
    free_dir = val_root / "FREE"

    if not model_path.exists():
        print(f"MODEL NOT FOUND: {model_path}")
        sys.exit(1)

    blocked_files = sorted(blocked_dir.glob("*.jpg"))
    free_files = sorted(free_dir.glob("*.jpg"))
    if not blocked_files or not free_files:
        print("VALIDATION DATASET MISSING")
        sys.exit(2)

    model = YOLO(str(model_path))
    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "BLOCKED" not in name_to_id or "FREE" not in name_to_id:
        print(f"BAD CLASS MAPPING: {model.names}")
        sys.exit(3)

    blocked_id = name_to_id["BLOCKED"]
    free_id = name_to_id["FREE"]

    rows = []
    for actual, files in [("BLOCKED", blocked_files), ("FREE", free_files)]:
        for p in files:
            r = model.predict(source=str(p), imgsz=IMGSZ, device=DEVICE, verbose=False)[0]
            rows.append({
                "actual": actual,
                "blocked_prob": float(r.probs.data[blocked_id]),
                "free_prob": float(r.probs.data[free_id]),
            })

    candidates = []

    print("=" * 82)
    print("Atlas Directional Release Freeze")
    print("=" * 82)
    print(" threshold | BLOCKED->FREE | FREE->BLOCKED | UNKNOWN")

    for t in THRESHOLDS:
        b2f = f2b = unknown = 0

        for row in rows:
            bp = row["blocked_prob"]
            fp = row["free_prob"]
            actual = row["actual"]

            if bp >= t:
                pred = "BLOCKED"
            elif fp >= t:
                pred = "FREE"
            else:
                pred = "UNKNOWN"

            if pred == "UNKNOWN":
                unknown += 1
            elif actual == "BLOCKED" and pred == "FREE":
                b2f += 1
            elif actual == "FREE" and pred == "BLOCKED":
                f2b += 1

        print(f"   {t:0.2f}    |      {b2f:3d}       |      {f2b:3d}       |   {unknown:3d}")

        if b2f == 0 and f2b == 0:
            candidates.append((unknown, t))

    if not candidates:
        print()
        print("FREEZE RESULT: FAIL - no zero-error tri-state threshold found.")
        sys.exit(4)

    candidates.sort()
    unknown, threshold = candidates[0]
    unknown_ratio = unknown / len(rows)

    if unknown_ratio > MAX_UNKNOWN_RATIO:
        print()
        print(f"FREEZE RESULT: FAIL - UNKNOWN ratio {unknown_ratio:.1%} exceeds {MAX_UNKNOWN_RATIO:.0%}.")
        print("Model/threshold needs more work before release.")
        sys.exit(5)

    release_dir = base / "Atlas_Models" / "RELEASE_CANDIDATES"
    release_dir.mkdir(parents=True, exist_ok=True)

    release_model = release_dir / "atlas_directional_release.pt"
    release_config = release_dir / "atlas_directional_release.json"

    shutil.copy2(model_path, release_model)

    config = {
        "model": release_model.name,
        "source_model": str(model_path),
        "task": "directional_traversability",
        "classes": ["BLOCKED", "FREE"],
        "imgsz": IMGSZ,
        "threshold": threshold,
        "zone_ranges": {
            "LEFT": [0.00, 0.42],
            "CENTER": [0.29, 0.71],
            "RIGHT": [0.58, 1.00]
        },
        "nav_top_ratio": 0.28,
        "unknown_rule": "If neither BLOCKED nor FREE probability reaches threshold, output UNKNOWN.",
        "unknown_behavior": "Do not advance into that zone; re-observe and re-evaluate.",
        "validation_blocked_count": len(blocked_files),
        "validation_free_count": len(free_files),
        "validation_unknown_at_threshold": unknown,
    }

    release_config.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print(f"SELECTED THRESHOLD : {threshold:.2f}")
    print(f"UNKNOWN ON VAL     : {unknown}/{len(rows)} ({unknown_ratio:.1%})")
    print(f"RELEASE MODEL      : {release_model}")
    print(f"RELEASE CONFIG     : {release_config}")
    print("FREEZE RESULT      : PASS")


if __name__ == "__main__":
    main()
