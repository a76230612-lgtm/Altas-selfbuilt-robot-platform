import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

HISTORY_SIZE = 5
MIN_VOTES = 3

SCENARIOS = {
    "directional_v2_tape":   {"CENTER": "FREE"},
    "directional_v2_center": {"CENTER": "BLOCKED"},
    "directional_v2_left":   {"CENTER": "FREE"},
    "directional_v2_right":  {"CENTER": "FREE"},
}

THRESHOLDS = [round(x / 100, 2) for x in range(50, 96)]


def latest_dir(root: Path, prefix: str):
    items = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    if not items:
        return None
    return max(items, key=lambda p: p.stat().st_mtime)


def raw_state(blocked_p, free_p, threshold):
    if blocked_p >= threshold:
        return "BLOCKED"
    if free_p >= threshold:
        return "FREE"
    return "UNKNOWN"


def stable(history):
    if len(history) < HISTORY_SIZE:
        return "UNKNOWN"

    c = Counter(history)

    if c["BLOCKED"] >= MIN_VOTES:
        return "BLOCKED"

    if c["FREE"] >= MIN_VOTES and c["BLOCKED"] == 0:
        return "FREE"

    return "UNKNOWN"


def simulate(rows, truth, threshold):
    h = deque(maxlen=HISTORY_SIZE)
    b_to_f = 0
    f_to_b = 0
    unknown = 0
    matches = 0

    for r in rows:
        bp = float(r["center_blocked_p"])
        fp = float(r["center_free_p"])

        raw = raw_state(bp, fp, threshold)
        h.append(raw)
        s = stable(h)

        if s == "UNKNOWN":
            unknown += 1
        elif truth == "BLOCKED" and s == "FREE":
            b_to_f += 1
        elif truth == "FREE" and s == "BLOCKED":
            f_to_b += 1

        if s == truth:
            matches += 1

    return {
        "b_to_f": b_to_f,
        "f_to_b": f_to_b,
        "unknown": unknown,
        "matches": matches,
        "total": len(rows),
    }


def main():
    base = Path(__file__).resolve().parent
    results_root = base / "Camera_Regression_Results"
    release_dir = base / "Atlas_Models" / "RELEASE_CANDIDATES"
    release_json = release_dir / "atlas_directional_release.json"

    print("=" * 94)
    print("Atlas 6.0 - CENTER Live Threshold Optimizer")
    print("=" * 94)

    if not release_json.exists():
        print("FAIL: missing directional release JSON:")
        print(release_json)
        raise SystemExit(1)

    dcfg = json.loads(release_json.read_text(encoding="utf-8"))
    base_threshold = float(dcfg["threshold"])

    loaded = {}
    source_folders = {}

    for prefix, truth_map in SCENARIOS.items():
        d = latest_dir(results_root, prefix)
        if d is None:
            print(f"FAIL: no regression folder found for {prefix}")
            raise SystemExit(2)

        csv_path = d / "regression.csv"
        if not csv_path.exists():
            print(f"FAIL: missing {csv_path}")
            raise SystemExit(3)

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            print(f"FAIL: empty CSV: {csv_path}")
            raise SystemExit(4)

        loaded[prefix] = rows
        source_folders[prefix] = str(d)

    print(f"Current global release threshold : {base_threshold:.2f}")
    print()
    print("Live source sets:")
    for prefix, d in source_folders.items():
        print(f"  {prefix:24s} -> {d}")

    print()
    print("Threshold sweep for CENTER only")
    print("-" * 94)
    print(f"{'THRESH':>7} {'B->F':>7} {'F->B':>7} {'UNKNOWN':>9} {'TOTAL':>7} {'MATCH_RATE':>12}")

    candidates = []

    for t in THRESHOLDS:
        agg = {"b_to_f": 0, "f_to_b": 0, "unknown": 0, "matches": 0, "total": 0}

        for prefix, truth_map in SCENARIOS.items():
            r = simulate(loaded[prefix], truth_map["CENTER"], t)
            for k in agg:
                agg[k] += r[k]

        rate = agg["matches"] / agg["total"] if agg["total"] else 0.0

        print(
            f"{t:7.2f} "
            f"{agg['b_to_f']:7d} "
            f"{agg['f_to_b']:7d} "
            f"{agg['unknown']:9d} "
            f"{agg['total']:7d} "
            f"{rate:12.3%}"
        )

        if agg["b_to_f"] == 0 and agg["f_to_b"] == 0:
            candidates.append((agg["unknown"], -agg["matches"], t, agg))

    print()
    print("=" * 94)

    if not candidates:
        print("CENTER THRESHOLD RESULT: FAIL")
        print("No single CENTER threshold gives zero BLOCKED->FREE and zero FREE->BLOCKED")
        print("on the four current live regression sets.")
        print()
        print("NEXT ACTION:")
        print("Do NOT retrain the whole Directional model.")
        print("Use a CENTER-only repair path (targeted CENTER hard positives or a dedicated CENTER model).")
        raise SystemExit(10)

    candidates.sort()
    unknown, neg_matches, chosen_t, chosen = candidates[0]
    unknown_rate = chosen["unknown"] / chosen["total"]
    match_rate = chosen["matches"] / chosen["total"]

    print("CENTER THRESHOLD RESULT: PASS")
    print(f"Recommended CENTER threshold : {chosen_t:.2f}")
    print(f"BLOCKED -> FREE             : {chosen['b_to_f']}")
    print(f"FREE -> BLOCKED             : {chosen['f_to_b']}")
    print(f"UNKNOWN                     : {chosen['unknown']}/{chosen['total']} ({unknown_rate:.2%})")
    print(f"Match rate                  : {match_rate:.2%}")

    # Conservative gate: do not write config if too much UNKNOWN.
    if unknown_rate > 0.20:
        print()
        print("CONFIG WRITE: SKIPPED")
        print("Reason: zero-error threshold exists, but UNKNOWN > 20%.")
        print("Do not lower LEFT/RIGHT thresholds and do not overwrite the current release.")
        raise SystemExit(11)

    config = {
        "schema": "atlas_directional_zone_thresholds_v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_release_json": str(release_json),
        "thresholds": {
            "LEFT": base_threshold,
            "CENTER": chosen_t,
            "RIGHT": base_threshold,
        },
        "safety_rule": {
            "BLOCKED_priority": True,
            "UNKNOWN_is_not_FREE": True,
            "history_size": HISTORY_SIZE,
            "min_votes": MIN_VOTES,
        },
        "center_live_validation": {
            "blocked_to_free": chosen["b_to_f"],
            "free_to_blocked": chosen["f_to_b"],
            "unknown": chosen["unknown"],
            "total": chosen["total"],
            "match_rate": match_rate,
            "source_folders": source_folders,
        },
    }

    out = release_dir / "atlas_directional_zone_thresholds.json"
    out.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("CONFIG WRITE: PASS")
    print(out)
    print()
    print("LEFT and RIGHT remain unchanged at the frozen release threshold.")
    print("Only CENTER receives the optimized live threshold.")


if __name__ == "__main__":
    main()
