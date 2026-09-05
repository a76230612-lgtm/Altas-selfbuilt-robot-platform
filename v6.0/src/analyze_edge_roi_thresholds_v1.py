import argparse
import csv
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224

THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def main():
    parser = argparse.ArgumentParser(
        description="Atlas EDGE ROI tri-state threshold analysis"
    )
    parser.add_argument("--model", required=True, help="Full path to ROI best.pt")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    dataset_root = base_dir / "Atlas_Edge_ROI_Dataset" / "val"
    edge_dir = dataset_root / "EDGE"
    safe_dir = dataset_root / "SAFE"

    if not model_path.exists():
        print(f"ERROR: model not found: {model_path}")
        sys.exit(1)

    edge_files = sorted(edge_dir.glob("*.jpg"))
    safe_files = sorted(safe_dir.glob("*.jpg"))

    if not edge_files or not safe_files:
        print("ERROR: validation EDGE/SAFE images not found.")
        sys.exit(2)

    model = YOLO(str(model_path))
    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        print(f"ERROR: expected EDGE/SAFE classes, got {model.names}")
        sys.exit(3)

    edge_id = name_to_id["EDGE"]
    safe_id = name_to_id["SAFE"]

    rows = []
    items = [("EDGE", p) for p in edge_files] + [("SAFE", p) for p in safe_files]

    print("=" * 88)
    print("Atlas 6.0 - EDGE ROI Threshold Analysis")
    print("=" * 88)
    print(f"Model    : {model_path}")
    print(f"VAL EDGE : {len(edge_files)}")
    print(f"VAL SAFE : {len(safe_files)}")
    print()
    print("Running inference once for all validation images...")

    for i, (actual, image_path) in enumerate(items, start=1):
        result = model.predict(
            source=str(image_path),
            imgsz=IMGSZ,
            device=DEVICE,
            verbose=False,
        )[0]

        probs = result.probs
        edge_prob = float(probs.data[edge_id])
        safe_prob = float(probs.data[safe_id])

        rows.append({
            "filename": image_path.name,
            "actual": actual,
            "edge_prob": edge_prob,
            "safe_prob": safe_prob,
        })

        print(f"[{i:02d}/{len(items)}] {actual:<4} {image_path.name}")

    print()
    print("=" * 88)
    print("TRI-STATE RULE")
    print("EDGE    if P(EDGE) >= threshold")
    print("SAFE    if P(SAFE) >= threshold")
    print("UNKNOWN otherwise")
    print("=" * 88)
    print()
    print(
        f"{'THRESH':>7} "
        f"{'E->S':>6} "
        f"{'S->E':>6} "
        f"{'UNKNOWN':>8} "
        f"{'KNOWN':>6} "
        f"{'KNOWN_ACC':>10}"
    )

    best = None

    for threshold in THRESHOLDS:
        edge_as_safe = 0
        safe_as_edge = 0
        unknown = 0
        known = 0
        known_correct = 0

        for row in rows:
            actual = row["actual"]
            ep = row["edge_prob"]
            sp = row["safe_prob"]

            if ep >= threshold:
                pred = "EDGE"
            elif sp >= threshold:
                pred = "SAFE"
            else:
                pred = "UNKNOWN"

            if pred == "UNKNOWN":
                unknown += 1
                continue

            known += 1

            if pred == actual:
                known_correct += 1
            elif actual == "EDGE" and pred == "SAFE":
                edge_as_safe += 1
            elif actual == "SAFE" and pred == "EDGE":
                safe_as_edge += 1

        known_acc = (known_correct / known) if known else 0.0

        print(
            f"{threshold:7.2f} "
            f"{edge_as_safe:6d} "
            f"{safe_as_edge:6d} "
            f"{unknown:8d} "
            f"{known:6d} "
            f"{known_acc:10.4f}"
        )

        candidate = {
            "threshold": threshold,
            "edge_as_safe": edge_as_safe,
            "safe_as_edge": safe_as_edge,
            "unknown": unknown,
            "known": known,
            "known_acc": known_acc,
        }

        # Deployment priority:
        # 1) zero critical EDGE->SAFE
        # 2) zero SAFE->EDGE if possible
        # 3) minimize UNKNOWN
        if edge_as_safe == 0 and safe_as_edge == 0:
            if best is None or unknown < best["unknown"]:
                best = candidate

    print()
    print("=" * 88)
    if best is not None:
        print("RECOMMENDED SAFETY THRESHOLD")
        print("=" * 88)
        print(f"Threshold                  : {best['threshold']:.2f}")
        print(f"EDGE -> SAFE               : {best['edge_as_safe']}")
        print(f"SAFE -> EDGE               : {best['safe_as_edge']}")
        print(f"UNKNOWN                    : {best['unknown']}")
        print(f"Known predictions          : {best['known']}")
        print(f"Known-prediction accuracy  : {best['known_acc']:.4f}")
        print()
        print("This threshold eliminates direct class mistakes on this validation set.")
        print("UNKNOWN must NEVER be treated as SAFE.")
    else:
        print("NO ZERO-ERROR TRI-STATE THRESHOLD FOUND")
        print("=" * 88)
        print("Use targeted hard-negative retraining before live deployment.")

    print()
    print("Misclassified-at-0.50 SAFE images:")
    for row in rows:
        if row["actual"] == "SAFE" and row["edge_prob"] >= 0.50:
            print(
                f"  {row['filename']} | "
                f"P(EDGE)={row['edge_prob']:.4f} "
                f"P(SAFE)={row['safe_prob']:.4f}"
            )

    print("=" * 88)


if __name__ == "__main__":
    main()
