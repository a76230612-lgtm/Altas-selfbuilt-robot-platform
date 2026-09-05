import argparse
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224
ROI_TOP_RATIO = 0.50
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
MAX_UNKNOWN_RATIO = 0.25


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Full path to passed EDGE ROI best.pt")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    val_root = base / "Atlas_Edge_ROI_Dataset" / "val"
    edge_dir = val_root / "EDGE"
    safe_dir = val_root / "SAFE"

    if not model_path.exists():
        print(f"MODEL NOT FOUND: {model_path}")
        sys.exit(1)

    edge_files = sorted(edge_dir.glob("*.jpg"))
    safe_files = sorted(safe_dir.glob("*.jpg"))
    if not edge_files or not safe_files:
        print("VALIDATION DATASET MISSING")
        sys.exit(2)

    model = YOLO(str(model_path))
    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}
    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        print(f"BAD CLASS MAPPING: {model.names}")
        sys.exit(3)

    edge_id = name_to_id["EDGE"]
    safe_id = name_to_id["SAFE"]

    rows = []
    for actual, files in [("EDGE", edge_files), ("SAFE", safe_files)]:
        for p in files:
            r = model.predict(source=str(p), imgsz=IMGSZ, device=DEVICE, verbose=False)[0]
            rows.append({
                "actual": actual,
                "edge_prob": float(r.probs.data[edge_id]),
                "safe_prob": float(r.probs.data[safe_id]),
            })

    candidates = []
    print("=" * 78)
    print("Atlas EDGE ROI Release Freeze")
    print("=" * 78)
    print(" threshold | EDGE->SAFE | SAFE->EDGE | UNKNOWN")
    for t in THRESHOLDS:
        e2s = s2e = unknown = 0
        for row in rows:
            ep, sp, actual = row["edge_prob"], row["safe_prob"], row["actual"]
            if ep >= t:
                pred = "EDGE"
            elif sp >= t:
                pred = "SAFE"
            else:
                pred = "UNKNOWN"

            if pred == "UNKNOWN":
                unknown += 1
            elif actual == "EDGE" and pred == "SAFE":
                e2s += 1
            elif actual == "SAFE" and pred == "EDGE":
                s2e += 1

        print(f"   {t:0.2f}    |     {e2s:3d}     |     {s2e:3d}     |   {unknown:3d}")
        if e2s == 0 and s2e == 0:
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

    release_model = release_dir / "atlas_edge_roi_release.pt"
    release_config = release_dir / "atlas_edge_roi_release.json"

    shutil.copy2(model_path, release_model)

    config = {
        "model": release_model.name,
        "source_model": str(model_path),
        "task": "global_edge_near_field_roi",
        "classes": ["EDGE", "SAFE"],
        "imgsz": IMGSZ,
        "roi_top_ratio": ROI_TOP_RATIO,
        "threshold": threshold,
        "unknown_rule": "If neither EDGE nor SAFE probability reaches threshold, output UNKNOWN.",
        "runtime_override": "If EDGE, set LEFT=EDGE, CENTER=EDGE, RIGHT=EDGE.",
        "unknown_behavior": "Do not advance; re-observe and re-evaluate.",
        "validation_edge_count": len(edge_files),
        "validation_safe_count": len(safe_files),
        "validation_unknown_at_threshold": unknown,
    }

    release_config.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"SELECTED THRESHOLD : {threshold:.2f}")
    print(f"UNKNOWN ON VAL     : {unknown}/{len(rows)} ({unknown_ratio:.1%})")
    print(f"RELEASE MODEL      : {release_model}")
    print(f"RELEASE CONFIG     : {release_config}")
    print("FREEZE RESULT      : PASS")


if __name__ == "__main__":
    main()
