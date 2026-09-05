import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

CAMERA_INDEX_DEFAULT = 1
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)
DEVICE = "cpu"
INFERENCE_FPS_DEFAULT = 5.0


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def open_camera(index: int):
    for name, backend in [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
        ("ANY", cv2.CAP_ANY),
    ]:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue

        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

        ok, frame = cap.read()
        if ok and frame is not None:
            print(f"CAMERA: PASS ({name})")
            return cap

        cap.release()

    return None


def letterbox_square(image, size=TARGET_SIZE):
    h, w = image.shape[:2]
    scale = min(size / w, size / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))

    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (nw, nh), interpolation=interp)

    left = (size - nw) // 2
    right = size - nw - left
    top = (size - nh) // 2
    bottom = size - nh - top

    return cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=PAD_COLOR,
    )


def crop_edge_roi(frame, roi_top_ratio):
    h, _ = frame.shape[:2]
    y1 = int(h * roi_top_ratio)
    return frame[y1:h, :].copy()


def edge_probabilities(model, image):
    result = model.predict(
        source=image,
        imgsz=TARGET_SIZE,
        device=DEVICE,
        verbose=False,
    )[0]

    names = {int(k): str(v).upper() for k, v in result.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if "EDGE" not in name_to_id or "SAFE" not in name_to_id:
        raise RuntimeError(f"Expected EDGE/SAFE classes, got {result.names}")

    p_edge = float(result.probs.data[name_to_id["EDGE"]])
    p_safe = float(result.probs.data[name_to_id["SAFE"]])

    return p_edge, p_safe


def percentile(values, q):
    return float(np.percentile(np.asarray(values, dtype=np.float32), q))


def build_summary(label, p_edges, p_safes, configured_threshold, seconds):
    return {
        "label": label,
        "seconds": seconds,
        "samples": len(p_edges),
        "configured_threshold": configured_threshold,
        "p_edge": {
            "min": float(min(p_edges)),
            "p05": percentile(p_edges, 5),
            "median": percentile(p_edges, 50),
            "p95": percentile(p_edges, 95),
            "max": float(max(p_edges)),
        },
        "p_safe": {
            "min": float(min(p_safes)),
            "p05": percentile(p_safes, 5),
            "median": percentile(p_safes, 50),
            "p95": percentile(p_safes, 95),
            "max": float(max(p_safes)),
        },
    }


def print_summary(summary):
    print()
    print("=" * 70)
    print(f"SUMMARY: {summary['label'].upper()}")
    print("=" * 70)
    print(f"Samples             : {summary['samples']}")
    print(f"Configured threshold: {summary['configured_threshold']:.3f}")

    pe = summary["p_edge"]
    ps = summary["p_safe"]

    print(
        "P_EDGE  "
        f"min={pe['min']:.3f} "
        f"p05={pe['p05']:.3f} "
        f"median={pe['median']:.3f} "
        f"p95={pe['p95']:.3f} "
        f"max={pe['max']:.3f}"
    )
    print(
        "P_SAFE  "
        f"min={ps['min']:.3f} "
        f"p05={ps['p05']:.3f} "
        f"median={ps['median']:.3f} "
        f"p95={ps['p95']:.3f} "
        f"max={ps['max']:.3f}"
    )


def compare_if_ready(output_dir: Path):
    safe_path = output_dir / "safe_summary.json"
    edge_path = output_dir / "edge_summary.json"

    if not safe_path.exists() or not edge_path.exists():
        return

    safe = json.loads(safe_path.read_text(encoding="utf-8"))
    edge = json.loads(edge_path.read_text(encoding="utf-8"))

    safe_floor_p05 = float(safe["p_safe"]["p05"])
    edge_scene_p95_safe = float(edge["p_safe"]["p95"])

    separation = safe_floor_p05 - edge_scene_p95_safe

    print()
    print("=" * 70)
    print("SAFE vs EDGE COMPARISON")
    print("=" * 70)
    print(f"SAFE-floor P_SAFE p05 : {safe_floor_p05:.3f}")
    print(f"EDGE-scene P_SAFE p95 : {edge_scene_p95_safe:.3f}")
    print(f"Safety separation      : {separation:.3f}")

    if separation >= 0.10:
        suggested = (safe_floor_p05 + edge_scene_p95_safe) / 2.0
        suggested = max(0.80, min(0.995, suggested))
        print("RESULT: SEPARABLE = YES")
        print(f"SUGGESTED SAFE-MIN confidence ≈ {suggested:.3f}")
        print(
            "NEXT: threshold/hysteresis can likely fix this without retraining."
        )
    else:
        print("RESULT: SEPARABLE = NO / TOO SMALL")
        print(
            "NEXT: do NOT trust threshold tuning alone. "
            "Use the saved EDGE hard-negative frames to retrain only the EDGE model."
        )

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Atlas 6.0 EDGE safety diagnostic. MOTOR MUST REMAIN DISARMED."
    )
    parser.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    parser.add_argument("--label", choices=["safe", "edge"], required=True)
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument(
        "--inference-fps",
        type=float,
        default=INFERENCE_FPS_DEFAULT,
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    release = base / "Atlas_Models" / "RELEASE_CANDIDATES"

    edge_pt = release / "atlas_edge_roi_release.pt"
    edge_json = release / "atlas_edge_roi_release.json"

    missing = [p for p in (edge_pt, edge_json) if not p.exists()]
    if missing:
        print("RELEASE FILE CHECK: FAIL")
        for p in missing:
            print("  MISSING:", p)
        sys.exit(1)

    cfg = load_json(edge_json)
    threshold = float(cfg["threshold"])
    roi_top_ratio = float(cfg["roi_top_ratio"])

    print("RELEASE FILE CHECK: PASS")
    print(f"Configured EDGE threshold : {threshold:.3f}")
    print(f"EDGE ROI top ratio        : {roi_top_ratio:.3f}")
    print()
    print("SAFETY:")
    print("  - This program NEVER sends ARM/AUTO/MOTOR commands.")
    print("  - Keep Atlas physically restrained / wheels off the ground.")
    print("  - For EDGE sample, do not allow the robot to roll toward the drop.")
    print()

    model = YOLO(str(edge_pt))
    print("EDGE MODEL: PASS")

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA: FAIL")
        sys.exit(2)

    # Warm camera.
    for _ in range(20):
        cap.read()

    output_dir = base / "edge_diagnostic"
    output_dir.mkdir(parents=True, exist_ok=True)

    hard_dir = output_dir / f"{args.label}_frames"
    hard_dir.mkdir(parents=True, exist_ok=True)

    interval = 1.0 / max(args.inference_fps, 0.5)
    end_time = time.monotonic() + max(args.seconds, 1.0)

    p_edges = []
    p_safes = []
    frame_records = []

    last_inference = 0.0
    sample_index = 0

    print()
    print(f"CAPTURING LABEL={args.label.upper()} FOR {args.seconds:.1f}s ...")
    print()

    try:
        while time.monotonic() < end_time:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            now = time.monotonic()
            if now - last_inference < interval:
                continue

            last_inference = now

            roi = crop_edge_roi(frame, roi_top_ratio)
            p_edge, p_safe = edge_probabilities(
                model,
                letterbox_square(roi),
            )

            p_edges.append(p_edge)
            p_safes.append(p_safe)

            prediction = "EDGE" if p_edge >= threshold else (
                "SAFE" if p_safe >= threshold else "UNKNOWN"
            )

            print(
                f"{sample_index:03d} | "
                f"P_EDGE={p_edge:.3f} "
                f"P_SAFE={p_safe:.3f} "
                f"RAW={prediction}"
            )

            # Save all diagnostic frames. These are useful as hard examples later.
            frame_path = hard_dir / f"{args.label}_{sample_index:03d}_safe_{p_safe:.3f}_edge_{p_edge:.3f}.jpg"
            cv2.imwrite(str(frame_path), frame)

            frame_records.append({
                "index": sample_index,
                "p_edge": p_edge,
                "p_safe": p_safe,
                "prediction": prediction,
                "frame": frame_path.name,
            })

            sample_index += 1

    finally:
        cap.release()

    if not p_edges:
        print("ERROR: No valid inference samples captured.")
        sys.exit(3)

    summary = build_summary(
        args.label,
        p_edges,
        p_safes,
        threshold,
        args.seconds,
    )

    summary_path = output_dir / f"{args.label}_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    records_path = output_dir / f"{args.label}_records.json"
    records_path.write_text(
        json.dumps(frame_records, indent=2),
        encoding="utf-8",
    )

    print_summary(summary)
    print()
    print(f"Saved summary : {summary_path}")
    print(f"Saved frames  : {hard_dir}")

    compare_if_ready(output_dir)


if __name__ == "__main__":
    main()
