import hashlib
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

DEVICE = "cpu"
IMGSZ = 224
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
MAX_UNKNOWN_RATIO = 0.25


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_directional_models(base: Path):
    models = []
    for p in base.rglob("best.pt"):
        low = str(p).lower()
        if "direction" in low and "release_candidates" not in low:
            models.append(p)
    return sorted(models, key=lambda p: p.stat().st_mtime, reverse=True)


def evaluate_model(model_path: Path, blocked_files, free_files):
    model = YOLO(str(model_path))

    names = {int(k): str(v).upper() for k, v in model.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "BLOCKED" not in name_to_id or "FREE" not in name_to_id:
        return {
            "valid_classes": False,
            "model": model_path,
            "classes": model.names,
        }

    blocked_id = name_to_id["BLOCKED"]
    free_id = name_to_id["FREE"]

    rows = []

    for actual, files in [("BLOCKED", blocked_files), ("FREE", free_files)]:
        for p in files:
            r = model.predict(
                source=str(p),
                imgsz=IMGSZ,
                device=DEVICE,
                verbose=False,
            )[0]

            rows.append({
                "actual": actual,
                "blocked_prob": float(r.probs.data[blocked_id]),
                "free_prob": float(r.probs.data[free_id]),
            })

    threshold_results = []

    for t in THRESHOLDS:
        b2f = 0
        f2b = 0
        unknown = 0
        known = 0
        known_correct = 0

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
                continue

            known += 1

            if pred == actual:
                known_correct += 1
            elif actual == "BLOCKED" and pred == "FREE":
                b2f += 1
            elif actual == "FREE" and pred == "BLOCKED":
                f2b += 1

        unknown_ratio = unknown / len(rows)
        known_acc = known_correct / known if known else 0.0

        threshold_results.append({
            "threshold": t,
            "blocked_as_free": b2f,
            "free_as_blocked": f2b,
            "unknown": unknown,
            "unknown_ratio": unknown_ratio,
            "known_accuracy": known_acc,
        })

    passing = [
        r for r in threshold_results
        if r["blocked_as_free"] == 0
        and r["free_as_blocked"] == 0
        and r["unknown_ratio"] <= MAX_UNKNOWN_RATIO
    ]

    best_pass = None
    if passing:
        best_pass = sorted(
            passing,
            key=lambda r: (r["unknown"], r["threshold"])
        )[0]

    # Best diagnostic fallback:
    # prioritize critical B->F, then total direct errors, then UNKNOWN.
    best_fallback = sorted(
        threshold_results,
        key=lambda r: (
            r["blocked_as_free"],
            r["blocked_as_free"] + r["free_as_blocked"],
            r["unknown"],
        ),
    )[0]

    return {
        "valid_classes": True,
        "model": model_path,
        "sha256": sha256(model_path),
        "mtime": model_path.stat().st_mtime,
        "size": model_path.stat().st_size,
        "best_pass": best_pass,
        "best_fallback": best_fallback,
        "threshold_results": threshold_results,
        "rows_count": len(rows),
    }


def main():
    base = Path(__file__).resolve().parent
    val_root = base / "Prepared_Atlas_Directional_Dataset" / "val"
    blocked_dir = val_root / "BLOCKED"
    free_dir = val_root / "FREE"

    blocked_files = sorted(blocked_dir.glob("*.jpg"))
    free_files = sorted(free_dir.glob("*.jpg"))

    print("=" * 92)
    print("Atlas 6.0 - Directional Release Resolver")
    print("=" * 92)
    print(f"Working folder : {base}")
    print(f"VAL BLOCKED    : {len(blocked_files)}")
    print(f"VAL FREE       : {len(free_files)}")
    print()

    if not blocked_files or not free_files:
        print("DATASET CHECK: FAIL")
        print("Prepared directional validation data is missing.")
        sys.exit(1)

    models = find_directional_models(base)

    if not models:
        print("MODEL CHECK: FAIL")
        print("No Directional best.pt was found.")
        sys.exit(2)

    print(f"Directional best.pt candidates found: {len(models)}")
    for p in models:
        print(f"  {p}")
    print()

    evaluated = []

    for idx, model_path in enumerate(models, start=1):
        print("-" * 92)
        print(f"[{idx}/{len(models)}] Evaluating:")
        print(model_path)

        result = evaluate_model(model_path, blocked_files, free_files)
        evaluated.append(result)

        if not result["valid_classes"]:
            print(f"  SKIP: wrong classes: {result['classes']}")
            continue

        print(f"  SHA256: {result['sha256'][:16]}...")
        print(f"  Size  : {result['size']} bytes")

        bp = result["best_pass"]

        if bp:
            print(
                "  PASS  : "
                f"T={bp['threshold']:.2f}, "
                f"B->F={bp['blocked_as_free']}, "
                f"F->B={bp['free_as_blocked']}, "
                f"UNKNOWN={bp['unknown']}/{result['rows_count']} "
                f"({bp['unknown_ratio']:.1%})"
            )
        else:
            fb = result["best_fallback"]
            print(
                "  FAIL  : best available "
                f"T={fb['threshold']:.2f}, "
                f"B->F={fb['blocked_as_free']}, "
                f"F->B={fb['free_as_blocked']}, "
                f"UNKNOWN={fb['unknown']}/{result['rows_count']} "
                f"({fb['unknown_ratio']:.1%})"
            )

    passing_models = [
        r for r in evaluated
        if r.get("valid_classes") and r.get("best_pass") is not None
    ]

    print()
    print("=" * 92)

    if not passing_models:
        print("FINAL RESULT: NO CURRENT DIRECTIONAL MODEL PASSES")
        print()
        print("This means the earlier PASS used a different model or a different validation set.")
        print("Do NOT freeze or enter live testing yet.")
        print()
        print("Next action: inspect the best failing model/error images and retrain only if needed.")
        sys.exit(10)

    # Rank by:
    # 1) fewest UNKNOWN
    # 2) lower threshold
    # 3) newest model
    passing_models.sort(
        key=lambda r: (
            r["best_pass"]["unknown"],
            r["best_pass"]["threshold"],
            -r["mtime"],
        )
    )

    winner = passing_models[0]
    model_path = winner["model"]
    selected = winner["best_pass"]

    print("PASSING MODEL FOUND")
    print(f"Selected model     : {model_path}")
    print(f"Selected SHA256    : {winner['sha256']}")
    print(f"Selected threshold : {selected['threshold']:.2f}")
    print(
        f"UNKNOWN            : {selected['unknown']}/{winner['rows_count']} "
        f"({selected['unknown_ratio']:.1%})"
    )
    print("BLOCKED -> FREE    : 0")
    print("FREE -> BLOCKED    : 0")
    print()

    release_dir = base / "Atlas_Models" / "RELEASE_CANDIDATES"
    release_dir.mkdir(parents=True, exist_ok=True)

    release_model = release_dir / "atlas_directional_release.pt"
    release_config = release_dir / "atlas_directional_release.json"

    shutil.copy2(model_path, release_model)

    config = {
        "model": release_model.name,
        "source_model": str(model_path),
        "source_model_sha256": winner["sha256"],
        "task": "directional_traversability",
        "classes": ["BLOCKED", "FREE"],
        "imgsz": IMGSZ,
        "threshold": selected["threshold"],
        "zone_ranges": {
            "LEFT": [0.00, 0.42],
            "CENTER": [0.29, 0.71],
            "RIGHT": [0.58, 1.00],
        },
        "nav_top_ratio": 0.28,
        "unknown_rule": (
            "If neither BLOCKED nor FREE probability reaches threshold, output UNKNOWN."
        ),
        "unknown_behavior": (
            "Do not advance into that zone; re-observe and re-evaluate."
        ),
        "validation_blocked_count": len(blocked_files),
        "validation_free_count": len(free_files),
        "validation_unknown_count": selected["unknown"],
        "validation_unknown_ratio": selected["unknown_ratio"],
        "blocked_as_free": 0,
        "free_as_blocked": 0,
    }

    release_config.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Release model      : {release_model}")
    print(f"Release config     : {release_config}")
    print()
    print("FREEZE RESULT      : PASS")
    print("=" * 92)


if __name__ == "__main__":
    main()
