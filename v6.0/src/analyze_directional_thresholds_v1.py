import argparse
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    model_path = Path(args.model).expanduser().resolve()
    val = base / "Prepared_Atlas_Directional_Dataset" / "val"
    blocked_files = sorted((val / "BLOCKED").glob("*.jpg"))
    free_files = sorted((val / "FREE").glob("*.jpg"))

    if not model_path.exists() or not blocked_files or not free_files:
        print("MODEL/DATA CHECK: FAIL")
        sys.exit(1)

    model = YOLO(str(model_path))
    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}
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

    best = None
    print("=" * 88)
    print("Directional Tri-state Threshold Analysis")
    print("=" * 88)
    print(f"{'THRESH':>7} {'B->F':>6} {'F->B':>6} {'UNKNOWN':>8} {'KNOWN':>6} {'KNOWN_ACC':>10}")

    for t in THRESHOLDS:
        b2f = f2b = unknown = known = correct = 0

        for row in rows:
            bp, fp, actual = row["blocked_prob"], row["free_prob"], row["actual"]
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
            if pred == actual:
                correct += 1
            elif actual == "BLOCKED" and pred == "FREE":
                b2f += 1
            elif actual == "FREE" and pred == "BLOCKED":
                f2b += 1

        known_acc = correct / known if known else 0.0
        print(f"{t:7.2f} {b2f:6d} {f2b:6d} {unknown:8d} {known:6d} {known_acc:10.4f}")

        if b2f == 0 and f2b == 0:
            candidate = (unknown, t, known_acc)
            if best is None or candidate < best:
                best = candidate

    print()
    if best:
        unknown, t, known_acc = best
        print("RECOMMENDED THRESHOLD")
        print(f"Threshold : {t:.2f}")
        print(f"UNKNOWN   : {unknown}/{len(rows)}")
        print(f"Known Acc : {known_acc:.4f}")
        print("THRESHOLD RESULT: PASS")
    else:
        print("THRESHOLD RESULT: NOT YET PASS")
        print("No zero-error tri-state threshold found.")


if __name__ == "__main__":
    main()
