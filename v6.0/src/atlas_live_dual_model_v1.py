import argparse
import csv
import json
import sys
import time
from collections import deque, Counter
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# ============================================================
# Atlas 6.0 - Stage 12A-3
# C950 Live Dual-Model Validation V1
#
# INPUTS
# - Atlas_Models/RELEASE_CANDIDATES/atlas_edge_roi_release.pt
# - Atlas_Models/RELEASE_CANDIDATES/atlas_edge_roi_release.json
# - Atlas_Models/RELEASE_CANDIDATES/atlas_directional_release.pt
# - Atlas_Models/RELEASE_CANDIDATES/atlas_directional_release.json
#
# CAMERA
# - EMEET C950
# - Camera index fixed at 1 by default
#
# SAFETY LOGIC
# 1. Global EDGE ROI model runs first.
# 2. EDGE stable -> LEFT/CENTER/RIGHT = EDGE.
# 3. EDGE UNKNOWN -> LEFT/CENTER/RIGHT = UNKNOWN.
# 4. EDGE SAFE -> run directional LEFT/CENTER/RIGHT.
# 5. Directional outputs FREE/BLOCKED/UNKNOWN.
# 6. 5-frame conservative temporal smoothing.
#
# IMPORTANT
# - NO ESP32.
# - NO ROS2.
# - NO MOTOR COMMANDS.
# - This is vision validation only.
# ============================================================


CAMERA_INDEX_DEFAULT = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)

HISTORY_SIZE = 5
MIN_VOTES = 3

DEVICE = "cpu"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def open_camera(index: int):
    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
        ("ANY", cv2.CAP_ANY),
    ]

    for name, backend in backends:
        print(f"Trying camera backend: {name}")
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
            print(f"Camera opened with backend: {name}")
            return cap

        cap.release()

    return None


def letterbox_square(image, size=TARGET_SIZE):
    h, w = image.shape[:2]
    if h <= 0 or w <= 0:
        raise ValueError("Invalid image dimensions")

    scale = min(size / w, size / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)

    left = (size - new_w) // 2
    right = size - new_w - left
    top = (size - new_h) // 2
    bottom = size - new_h - top

    return cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=PAD_COLOR,
    )


def class_probabilities(model, image, class_a, class_b):
    result = model.predict(
        source=image,
        imgsz=TARGET_SIZE,
        device=DEVICE,
        verbose=False,
    )[0]

    names = {int(k): str(v).upper() for k, v in result.names.items()}
    name_to_id = {v: k for k, v in names.items()}

    if class_a not in name_to_id or class_b not in name_to_id:
        raise RuntimeError(
            f"Expected classes {class_a}/{class_b}, got {result.names}"
        )

    p_a = float(result.probs.data[name_to_id[class_a]])
    p_b = float(result.probs.data[name_to_id[class_b]])
    return p_a, p_b


def tri_state(prob_a, prob_b, threshold, label_a, label_b):
    # Binary softmax means both cannot exceed >0.5 thresholds simultaneously.
    if prob_a >= threshold:
        return label_a
    if prob_b >= threshold:
        return label_b
    return "UNKNOWN"


def conservative_stable(history, positive_label, negative_label):
    """
    Conservative 5-frame rule.

    positive_label is the safety-blocking state:
      EDGE for global model
      BLOCKED for directional model

    Rules:
    - History must be full before a stable non-UNKNOWN result.
    - >=3 positive votes -> positive.
    - Negative is allowed only if:
        >=3 negative votes AND zero positive votes.
    - Otherwise UNKNOWN.
    """
    if len(history) < HISTORY_SIZE:
        return "UNKNOWN"

    counts = Counter(history)

    if counts[positive_label] >= MIN_VOTES:
        return positive_label

    if counts[negative_label] >= MIN_VOTES and counts[positive_label] == 0:
        return negative_label

    return "UNKNOWN"


def crop_edge_roi(frame, roi_top_ratio):
    h, _ = frame.shape[:2]
    y1 = int(h * roi_top_ratio)
    return frame[y1:h, :].copy(), y1


def crop_direction_zone(frame, nav_top_ratio, x1_ratio, x2_ratio):
    h, w = frame.shape[:2]
    y1 = int(h * nav_top_ratio)
    x1 = int(w * x1_ratio)
    x2 = int(w * x2_ratio)
    return frame[y1:h, x1:x2].copy(), (x1, y1, x2, h)


def color_for_state(state):
    # BGR display colors only.
    if state in ("EDGE", "BLOCKED"):
        return (0, 0, 255)
    if state in ("SAFE", "FREE"):
        return (0, 220, 0)
    return (0, 200, 255)


def write_text(img, text, x, y, scale=0.62, thickness=2, color=(255, 255, 255)):
    cv2.putText(
        img,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    parser.add_argument(
        "--seconds",
        type=int,
        default=120,
        help="Auto-stop duration in seconds. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--inference-fps",
        type=float,
        default=5.0,
        help="Model inference frequency. Default 5 Hz.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    release_dir = base_dir / "Atlas_Models" / "RELEASE_CANDIDATES"

    edge_model_path = release_dir / "atlas_edge_roi_release.pt"
    edge_config_path = release_dir / "atlas_edge_roi_release.json"
    dir_model_path = release_dir / "atlas_directional_release.pt"
    dir_config_path = release_dir / "atlas_directional_release.json"

    required = [
        edge_model_path,
        edge_config_path,
        dir_model_path,
        dir_config_path,
    ]

    print("=" * 86)
    print("Atlas 6.0 - Stage 12A-3 C950 Live Dual-Model Validation V1")
    print("=" * 86)

    missing = [p for p in required if not p.exists()]
    if missing:
        print("RELEASE FILE CHECK: FAIL")
        for p in missing:
            print(f"  MISSING: {p}")
        sys.exit(1)

    print("RELEASE FILE CHECK: PASS")

    edge_cfg = load_json(edge_config_path)
    dir_cfg = load_json(dir_config_path)

    edge_threshold = float(edge_cfg["threshold"])
    edge_roi_top = float(edge_cfg["roi_top_ratio"])

    dir_threshold = float(dir_cfg["threshold"])
    nav_top_ratio = float(dir_cfg.get("nav_top_ratio", 0.28))
    zone_ranges = dir_cfg["zone_ranges"]

    print(f"EDGE threshold       : {edge_threshold:.2f}")
    print(f"EDGE ROI top ratio   : {edge_roi_top:.2f}")
    print(f"Directional threshold: {dir_threshold:.2f}")
    print(f"Directional nav top  : {nav_top_ratio:.2f}")
    print()

    edge_model = YOLO(str(edge_model_path))
    dir_model = YOLO(str(dir_model_path))

    print("MODELS LOADED: PASS")

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA CHECK: FAIL")
        print("Close Camera / Teams / Zoom / browser camera pages and retry.")
        sys.exit(2)

    print("CAMERA CHECK: PASS")
    print()
    print("NO MOTOR CONTROL IS ACTIVE.")
    print("The test auto-stops after the selected duration.")
    print("Ctrl+C can also stop it safely.")
    print()

    # Warm-up camera.
    for _ in range(30):
        cap.read()

    # Warm-up models with first usable frame.
    ok, warm = cap.read()
    if not ok or warm is None:
        print("CAMERA FRAME CHECK: FAIL")
        cap.release()
        sys.exit(3)

    edge_roi, _ = crop_edge_roi(warm, edge_roi_top)
    edge_input = letterbox_square(edge_roi)
    class_probabilities(edge_model, edge_input, "EDGE", "SAFE")

    for zone_name in ("LEFT", "CENTER", "RIGHT"):
        x1r, x2r = zone_ranges[zone_name]
        z, _ = crop_direction_zone(warm, nav_top_ratio, x1r, x2r)
        z_input = letterbox_square(z)
        class_probabilities(dir_model, z_input, "BLOCKED", "FREE")

    print("MODEL WARM-UP: PASS")
    print()

    histories = {
        "EDGE": deque(maxlen=HISTORY_SIZE),
        "LEFT": deque(maxlen=HISTORY_SIZE),
        "CENTER": deque(maxlen=HISTORY_SIZE),
        "RIGHT": deque(maxlen=HISTORY_SIZE),
    }

    raw_edge = "UNKNOWN"
    stable_edge = "UNKNOWN"
    edge_p = 0.0
    safe_p = 0.0

    raw_dir = {z: "UNKNOWN" for z in ("LEFT", "CENTER", "RIGHT")}
    stable_dir = {z: "UNKNOWN" for z in ("LEFT", "CENTER", "RIGHT")}
    blocked_p = {z: 0.0 for z in ("LEFT", "CENTER", "RIGHT")}
    free_p = {z: 0.0 for z in ("LEFT", "CENTER", "RIGHT")}

    log_dir = base_dir / "Live_Validation_Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = log_dir / f"stage12A3_live_{run_id}.csv"

    csv_file = csv_path.open("w", newline="", encoding="utf-8-sig")
    fieldnames = [
        "timestamp",
        "edge_raw",
        "edge_stable",
        "edge_probability",
        "safe_probability",
        "left_raw",
        "left_stable",
        "left_blocked_probability",
        "left_free_probability",
        "center_raw",
        "center_stable",
        "center_blocked_probability",
        "center_free_probability",
        "right_raw",
        "right_stable",
        "right_blocked_probability",
        "right_free_probability",
        "final_left",
        "final_center",
        "final_right",
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    start_time = time.time()
    last_inference = 0.0
    inference_interval = 1.0 / max(args.inference_fps, 0.5)

    state_counts = Counter()
    frames_logged = 0

    window_name = "Atlas 6.0 - Stage 12A-3 Live Vision Validation"

    try:
        while True:
            now = time.time()

            if args.seconds > 0 and now - start_time >= args.seconds:
                print()
                print("AUTO-STOP: requested test duration reached.")
                break

            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            # Only run models at configured inference rate.
            if now - last_inference >= inference_interval:
                last_inference = now

                # ------------------------------------------------
                # 1) Global EDGE ROI
                # ------------------------------------------------
                edge_roi, edge_y1 = crop_edge_roi(frame, edge_roi_top)
                edge_input = letterbox_square(edge_roi)

                edge_p, safe_p = class_probabilities(
                    edge_model,
                    edge_input,
                    "EDGE",
                    "SAFE",
                )

                raw_edge = tri_state(
                    edge_p,
                    safe_p,
                    edge_threshold,
                    "EDGE",
                    "SAFE",
                )

                histories["EDGE"].append(raw_edge)
                stable_edge = conservative_stable(
                    histories["EDGE"],
                    positive_label="EDGE",
                    negative_label="SAFE",
                )

                # ------------------------------------------------
                # 2) Directional model
                # Run when global EDGE is not stably EDGE.
                # This allows us to observe the model during SAFE/UNKNOWN,
                # but final outputs remain safety-gated below.
                # ------------------------------------------------
                for zone_name in ("LEFT", "CENTER", "RIGHT"):
                    x1r, x2r = zone_ranges[zone_name]
                    zone_crop, _ = crop_direction_zone(
                        frame,
                        nav_top_ratio,
                        x1r,
                        x2r,
                    )
                    zone_input = letterbox_square(zone_crop)

                    bp, fp = class_probabilities(
                        dir_model,
                        zone_input,
                        "BLOCKED",
                        "FREE",
                    )

                    blocked_p[zone_name] = bp
                    free_p[zone_name] = fp

                    raw = tri_state(
                        bp,
                        fp,
                        dir_threshold,
                        "BLOCKED",
                        "FREE",
                    )

                    raw_dir[zone_name] = raw
                    histories[zone_name].append(raw)

                    stable_dir[zone_name] = conservative_stable(
                        histories[zone_name],
                        positive_label="BLOCKED",
                        negative_label="FREE",
                    )

                # ------------------------------------------------
                # 3) Final safety-gated outputs
                # ------------------------------------------------
                if stable_edge == "EDGE":
                    final = {
                        "LEFT": "EDGE",
                        "CENTER": "EDGE",
                        "RIGHT": "EDGE",
                    }

                elif stable_edge == "UNKNOWN":
                    final = {
                        "LEFT": "UNKNOWN",
                        "CENTER": "UNKNOWN",
                        "RIGHT": "UNKNOWN",
                    }

                else:  # stable EDGE model says SAFE
                    final = dict(stable_dir)

                state_counts[f"EDGE_STABLE_{stable_edge}"] += 1
                for z in ("LEFT", "CENTER", "RIGHT"):
                    state_counts[f"{z}_FINAL_{final[z]}"] += 1

                writer.writerow({
                    "timestamp": datetime.now().isoformat(timespec="milliseconds"),
                    "edge_raw": raw_edge,
                    "edge_stable": stable_edge,
                    "edge_probability": f"{edge_p:.6f}",
                    "safe_probability": f"{safe_p:.6f}",
                    "left_raw": raw_dir["LEFT"],
                    "left_stable": stable_dir["LEFT"],
                    "left_blocked_probability": f"{blocked_p['LEFT']:.6f}",
                    "left_free_probability": f"{free_p['LEFT']:.6f}",
                    "center_raw": raw_dir["CENTER"],
                    "center_stable": stable_dir["CENTER"],
                    "center_blocked_probability": f"{blocked_p['CENTER']:.6f}",
                    "center_free_probability": f"{free_p['CENTER']:.6f}",
                    "right_raw": raw_dir["RIGHT"],
                    "right_stable": stable_dir["RIGHT"],
                    "right_blocked_probability": f"{blocked_p['RIGHT']:.6f}",
                    "right_free_probability": f"{free_p['RIGHT']:.6f}",
                    "final_left": final["LEFT"],
                    "final_center": final["CENTER"],
                    "final_right": final["RIGHT"],
                })
                csv_file.flush()
                frames_logged += 1

            # ----------------------------------------------------
            # Display overlay
            # ----------------------------------------------------
            display = frame.copy()
            h, w = display.shape[:2]

            # EDGE ROI rectangle.
            edge_y1 = int(h * edge_roi_top)
            edge_color = color_for_state(stable_edge)
            cv2.rectangle(
                display,
                (0, edge_y1),
                (w - 1, h - 1),
                edge_color,
                3,
            )

            write_text(
                display,
                f"EDGE raw={raw_edge} stable={stable_edge} "
                f"P(E)={edge_p:.2f} P(S)={safe_p:.2f} T={edge_threshold:.2f}",
                15,
                30,
                scale=0.58,
                color=edge_color,
            )

            # Directional rectangles and labels.
            final_for_display = {}
            if stable_edge == "EDGE":
                final_for_display = {z: "EDGE" for z in ("LEFT", "CENTER", "RIGHT")}
            elif stable_edge == "UNKNOWN":
                final_for_display = {z: "UNKNOWN" for z in ("LEFT", "CENTER", "RIGHT")}
            else:
                final_for_display = dict(stable_dir)

            nav_y1 = int(h * nav_top_ratio)

            y_positions = {
                "LEFT": 70,
                "CENTER": 100,
                "RIGHT": 130,
            }

            for zone_name in ("LEFT", "CENTER", "RIGHT"):
                x1r, x2r = zone_ranges[zone_name]
                x1 = int(w * x1r)
                x2 = int(w * x2r)

                state = final_for_display[zone_name]
                color = color_for_state(state)

                cv2.rectangle(
                    display,
                    (x1, nav_y1),
                    (x2 - 1, h - 1),
                    color,
                    2,
                )

                write_text(
                    display,
                    f"{zone_name}: final={state} raw={raw_dir[zone_name]} "
                    f"B={blocked_p[zone_name]:.2f} F={free_p[zone_name]:.2f}",
                    15,
                    y_positions[zone_name],
                    scale=0.54,
                    color=color,
                )

            elapsed = now - start_time
            remaining = max(0, args.seconds - int(elapsed)) if args.seconds > 0 else -1

            if remaining >= 0:
                timer_text = f"Auto-stop in {remaining}s | inference {args.inference_fps:.1f} Hz"
            else:
                timer_text = f"Unlimited | inference {args.inference_fps:.1f} Hz"

            write_text(
                display,
                timer_text,
                15,
                h - 15,
                scale=0.55,
                color=(255, 255, 255),
            )

            cv2.imshow(window_name, display)

            # Optional convenience only; Ctrl+C and auto-stop are primary.
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                print()
                print("Window stop key received.")
                break

    except KeyboardInterrupt:
        print()
        print("Ctrl+C received. Test stopped safely.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        csv_file.close()

    print()
    print("=" * 86)
    print("LIVE VALIDATION SUMMARY")
    print("=" * 86)
    print(f"Inference records : {frames_logged}")
    print(f"CSV log           : {csv_path}")
    print()
    for key in sorted(state_counts):
        print(f"{key:<35} : {state_counts[key]}")
    print()
    print("NO MOTOR COMMANDS WERE SENT.")
    print("STAGE 12A-3 LIVE RUN: COMPLETE")
    print("=" * 86)


if __name__ == "__main__":
    main()
