import csv
from collections import Counter
from pathlib import Path
from statistics import mean

SCENARIOS = [
    "tape_empty_v2",
    "center_obstacle_v2",
    "left_obstacle_v2",
    "right_obstacle_v2",
]

EXPECTED = {
    "tape_empty_v2": ("SAFE", "FREE", "FREE", "FREE"),
    "center_obstacle_v2": ("SAFE", "FREE", "BLOCKED", "FREE"),
    "left_obstacle_v2": ("SAFE", "BLOCKED", "FREE", "FREE"),
    "right_obstacle_v2": ("SAFE", "FREE", "FREE", "BLOCKED"),
}


def latest_dir(root: Path, prefix: str):
    candidates = sorted(
        [p for p in root.glob(prefix + "_*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def fnum(row, key):
    try:
        return float(row[key])
    except Exception:
        return float("nan")


def fmt_counter(c: Counter):
    return ", ".join(f"{k}={v}" for k, v in c.most_common())


def main():
    base = Path(__file__).resolve().parent
    root = base / "Camera_Regression_Results"

    print("=" * 100)
    print("Atlas 6.0 - Camera Regression Root-Cause Analyzer V2")
    print("=" * 100)

    if not root.exists():
        print("FAIL: Camera_Regression_Results folder not found:")
        print(root)
        return

    for scenario in SCENARIOS:
        d = latest_dir(root, scenario)
        if d is None:
            print(f"\n[{scenario}] NOT FOUND")
            continue

        csv_path = d / "regression.csv"
        if not csv_path.exists():
            print(f"\n[{scenario}] regression.csv NOT FOUND")
            continue

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        print("\n" + "-" * 100)
        print(f"SCENARIO : {scenario}")
        print(f"FOLDER   : {d}")
        print(f"ROWS     : {len(rows)}")
        print(
            f"EXPECTED : EDGE={EXPECTED[scenario][0]} "
            f"L/C/R={EXPECTED[scenario][1]}/{EXPECTED[scenario][2]}/{EXPECTED[scenario][3]}"
        )

        if not rows:
            print("No rows.")
            continue

        edge_stable = Counter(r["edge_stable"] for r in rows)
        edge_raw = Counter(r["edge_raw"] for r in rows)
        final_patterns = Counter(
            (r["final_left"], r["final_center"], r["final_right"]) for r in rows
        )
        dir_patterns = Counter(
            (r["left_stable"], r["center_stable"], r["right_stable"]) for r in rows
        )

        print("EDGE stable counts :", fmt_counter(edge_stable))
        print("EDGE raw counts    :", fmt_counter(edge_raw))

        print("Dominant FINAL patterns:")
        for pat, count in final_patterns.most_common(5):
            print(f"  {pat} -> {count}/{len(rows)} ({count/len(rows):.1%})")

        print("Dominant DIRECTIONAL-stable patterns BEFORE EDGE gating:")
        for pat, count in dir_patterns.most_common(5):
            print(f"  {pat} -> {count}/{len(rows)} ({count/len(rows):.1%})")

        edge_p = [fnum(r, "edge_p") for r in rows]
        safe_p = [fnum(r, "safe_p") for r in rows]
        left_b = [fnum(r, "left_blocked_p") for r in rows]
        left_f = [fnum(r, "left_free_p") for r in rows]
        center_b = [fnum(r, "center_blocked_p") for r in rows]
        center_f = [fnum(r, "center_free_p") for r in rows]
        right_b = [fnum(r, "right_blocked_p") for r in rows]
        right_f = [fnum(r, "right_free_p") for r in rows]

        print("Mean EDGE probabilities:")
        print(f"  P(EDGE)={mean(edge_p):.4f}  P(SAFE)={mean(safe_p):.4f}")

        print("Mean Directional probabilities:")
        print(f"  LEFT   P(BLOCKED)={mean(left_b):.4f} P(FREE)={mean(left_f):.4f}")
        print(f"  CENTER P(BLOCKED)={mean(center_b):.4f} P(FREE)={mean(center_f):.4f}")
        print(f"  RIGHT  P(BLOCKED)={mean(right_b):.4f} P(FREE)={mean(right_f):.4f}")

        expected_final = EXPECTED[scenario][1:]
        dominant_final, dominant_final_count = final_patterns.most_common(1)[0]
        dominant_dir, dominant_dir_count = dir_patterns.most_common(1)[0]

        edge_safe = edge_stable["SAFE"]
        edge_edge = edge_stable["EDGE"]
        edge_unknown = edge_stable["UNKNOWN"]

        if edge_edge >= 0.80 * len(rows):
            hint = "GLOBAL_EDGE_FALSE_POSITIVE"
        elif edge_safe >= 0.80 * len(rows):
            if dominant_dir_count >= 0.80 * len(rows) and dominant_dir != expected_final:
                hint = "DIRECTIONAL_WRONG_STABLE_PATTERN"
            elif dominant_final == expected_final:
                hint = "MOSTLY_CORRECT"
            else:
                hint = "DIRECTIONAL_OR_GATING_MISMATCH"
        elif edge_unknown >= 0.30 * len(rows):
            hint = "GLOBAL_EDGE_UNSTABLE_UNKNOWN"
        else:
            hint = "MIXED_NEEDS_INSPECTION"

        print(f"ROOT-CAUSE HINT     : {hint}")

    print("\n" + "=" * 100)
    print("FINAL DECISION GUIDE")
    print("=" * 100)
    print("GLOBAL_EDGE_FALSE_POSITIVE -> do not retrain Directional.")
    print("DIRECTIONAL_WRONG_STABLE_PATTERN -> inspect crop/model/release identity before retraining.")
    print("GLOBAL_EDGE_UNSTABLE_UNKNOWN -> investigate EDGE confidence/ROI.")
    print("Do not retrain anything until this output identifies the branch.")


if __name__ == "__main__":
    main()
