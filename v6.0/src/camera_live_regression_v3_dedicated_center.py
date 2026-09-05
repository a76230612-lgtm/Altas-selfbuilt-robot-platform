"""
Atlas 6.0 - Live Regression V3
--------------------------------
Architecture:
  EDGE     -> existing atlas_edge_roi_release
  LEFT     -> existing atlas_directional_release
  CENTER   -> dedicated atlas_center_release
  RIGHT    -> existing atlas_directional_release

This isolates CENTER repair from already-passing LEFT/RIGHT behavior.
"""

import argparse
import csv
import json
import sys
import time
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

CAMERA_INDEX_DEFAULT = 1
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
DEVICE = "cpu"
IMGSZ = 224
PAD_COLOR = (114, 114, 114)
HISTORY_SIZE = 5
MIN_VOTES = 3


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def open_camera(index):
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
            print(f"CAMERA BACKEND: {name}")
            return cap
        cap.release()
    return None


def letterbox_square(image, size=IMGSZ):
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
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=PAD_COLOR
    )


def probs_for(model, image, a, b):
    r = model.predict(
        source=image, imgsz=IMGSZ,
        device=DEVICE, verbose=False
    )[0]

    names = {int(k): str(v).upper() for k, v in r.names.items()}
    ids = {v: k for k, v in names.items()}

    return (
        float(r.probs.data[ids[a]]),
        float(r.probs.data[ids[b]])
    )


def tri_state(pa, pb, threshold, a, b):
    if pa >= threshold:
        return a
    if pb >= threshold:
        return b
    return "UNKNOWN"


def stable(history, danger, clear):
    if len(history) < HISTORY_SIZE:
        return "UNKNOWN"

    c = Counter(history)

    if c[danger] >= MIN_VOTES:
        return danger

    if c[clear] >= MIN_VOTES and c[danger] == 0:
        return clear

    return "UNKNOWN"


def crop_zone(frame, nav_top, zone):
    h, w = frame.shape[:2]
    x1 = int(round(w * zone[0]))
    x2 = int(round(w * zone[1]))
    y1 = int(round(h * nav_top))
    return frame[y1:h, x1:x2].copy(), (x1, y1, x2, h)


def crop_edge(frame, roi_top):
    h, w = frame.shape[:2]
    y1 = int(round(h * roi_top))
    return frame[y1:h, :].copy()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", required=True)
    p.add_argument("--edge", required=True, choices=["SAFE", "EDGE"])
    p.add_argument("--left", required=True, choices=["FREE", "BLOCKED"])
    p.add_argument("--center", required=True, choices=["FREE", "BLOCKED"])
    p.add_argument("--right", required=True, choices=["FREE", "BLOCKED"])
    p.add_argument("--seconds", type=int, default=20)
    p.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    p.add_argument("--inference-fps", type=float, default=5.0)
    args = p.parse_args()

    base = Path(__file__).resolve().parent
    rel = base / "Atlas_Models" / "RELEASE_CANDIDATES"

    edge_pt = rel / "atlas_edge_roi_release.pt"
    edge_js = rel / "atlas_edge_roi_release.json"
    dir_pt = rel / "atlas_directional_release.pt"
    dir_js = rel / "atlas_directional_release.json"
    center_pt = rel / "atlas_center_release.pt"
    center_js = rel / "atlas_center_release.json"

    required = [
        edge_pt, edge_js,
        dir_pt, dir_js,
        center_pt, center_js
    ]

    missing = [p for p in required if not p.exists()]
    if missing:
        print("RELEASE FILE CHECK: FAIL")
        for m in missing:
            print("MISSING:", m)
        raise SystemExit(1)

    ecfg = load_json(edge_js)
    dcfg = load_json(dir_js)
    ccfg = load_json(center_js)

    edge_t = float(ecfg["threshold"])
    edge_roi_top = float(ecfg["roi_top_ratio"])

    side_t = float(dcfg["threshold"])
    center_t = float(ccfg["threshold"])

    nav_top = float(dcfg["nav_top_ratio"])
    zones = dcfg["zone_ranges"]

    print("=" * 92)
    print("Atlas 6.0 - Live Regression V3 | Dedicated CENTER Model")
    print("=" * 92)
    print(f"Scenario         : {args.scenario}")
    print(f"Expected EDGE    : {args.edge}")
    print(f"Expected L/C/R   : {args.left}/{args.center}/{args.right}")
    print(f"EDGE threshold   : {edge_t}")
    print(f"LEFT threshold   : {side_t}  [Directional V2]")
    print(f"CENTER threshold : {center_t}  [Dedicated CENTER]")
    print(f"RIGHT threshold  : {side_t}  [Directional V2]")
    print()

    edge_model = YOLO(str(edge_pt))
    side_model = YOLO(str(dir_pt))
    center_model = YOLO(str(center_pt))

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA CHECK: FAIL")
        raise SystemExit(2)

    for _ in range(30):
        cap.read()

    histories = {
        "EDGE": deque(maxlen=HISTORY_SIZE),
        "LEFT": deque(maxlen=HISTORY_SIZE),
        "CENTER": deque(maxlen=HISTORY_SIZE),
        "RIGHT": deque(maxlen=HISTORY_SIZE),
    }

    records = matches = mismatch = unknown = 0
    transitions = {k: 0 for k in histories}
    previous = {k: None for k in histories}

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = (
        base / "Camera_Regression_Results" /
        f"{args.scenario}_{run_id}"
    )
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / "regression.csv"
    f = csv_path.open("w", newline="", encoding="utf-8-sig")
    writer = csv.writer(f)
    writer.writerow([
        "time",
        "edge_stable",
        "left_stable",
        "center_stable",
        "right_stable",
        "edge_p", "safe_p",
        "left_blocked_p", "left_free_p",
        "center_blocked_p", "center_free_p",
        "right_blocked_p", "right_free_p",
        "match"
    ])

    start = time.time()
    last_infer = 0.0
    interval = 1.0 / max(args.inference_fps, 0.5)

    try:
        while time.time() - start < args.seconds:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            now = time.time()
            if now - last_infer < interval:
                cv2.imshow("Atlas Live Regression V3", frame)
                cv2.waitKey(1)
                continue

            last_infer = now

            edge_crop = crop_edge(frame, edge_roi_top)
            ep, sp = probs_for(
                edge_model,
                letterbox_square(edge_crop),
                "EDGE", "SAFE"
            )
            edge_raw = tri_state(ep, sp, edge_t, "EDGE", "SAFE")
            histories["EDGE"].append(edge_raw)
            edge_st = stable(histories["EDGE"], "EDGE", "SAFE")

            values = {}

            for zone in ["LEFT", "RIGHT"]:
                crop, _ = crop_zone(frame, nav_top, zones[zone])
                bp, fp = probs_for(
                    side_model,
                    letterbox_square(crop),
                    "BLOCKED", "FREE"
                )
                raw = tri_state(
                    bp, fp, side_t,
                    "BLOCKED", "FREE"
                )
                histories[zone].append(raw)
                st = stable(
                    histories[zone],
                    "BLOCKED", "FREE"
                )
                values[zone] = (bp, fp, st)

            crop, _ = crop_zone(
                frame, nav_top, zones["CENTER"]
            )
            cbp, cfp = probs_for(
                center_model,
                letterbox_square(crop),
                "BLOCKED", "FREE"
            )
            center_raw = tri_state(
                cbp, cfp, center_t,
                "BLOCKED", "FREE"
            )
            histories["CENTER"].append(center_raw)
            center_st = stable(
                histories["CENTER"],
                "BLOCKED", "FREE"
            )
            values["CENTER"] = (cbp, cfp, center_st)

            if edge_st == "EDGE":
                final = {
                    "LEFT": "EDGE",
                    "CENTER": "EDGE",
                    "RIGHT": "EDGE"
                }
            elif edge_st == "UNKNOWN":
                final = {
                    "LEFT": "UNKNOWN",
                    "CENTER": "UNKNOWN",
                    "RIGHT": "UNKNOWN"
                }
            else:
                final = {
                    "LEFT": values["LEFT"][2],
                    "CENTER": values["CENTER"][2],
                    "RIGHT": values["RIGHT"][2]
                }

            current = {
                "EDGE": edge_st,
                "LEFT": final["LEFT"],
                "CENTER": final["CENTER"],
                "RIGHT": final["RIGHT"],
            }

            for k in current:
                if previous[k] is not None and current[k] != previous[k]:
                    transitions[k] += 1
                previous[k] = current[k]

            is_match = (
                edge_st == args.edge and
                final["LEFT"] == args.left and
                final["CENTER"] == args.center and
                final["RIGHT"] == args.right
            )

            records += 1
            if is_match:
                matches += 1
            else:
                mismatch += 1

            if (
                edge_st == "UNKNOWN" or
                "UNKNOWN" in final.values()
            ):
                unknown += 1

            writer.writerow([
                datetime.now().isoformat(timespec="milliseconds"),
                edge_st,
                final["LEFT"],
                final["CENTER"],
                final["RIGHT"],
                f"{ep:.6f}", f"{sp:.6f}",
                f"{values['LEFT'][0]:.6f}",
                f"{values['LEFT'][1]:.6f}",
                f"{values['CENTER'][0]:.6f}",
                f"{values['CENTER'][1]:.6f}",
                f"{values['RIGHT'][0]:.6f}",
                f"{values['RIGHT'][1]:.6f}",
                "PASS" if is_match else "FAIL"
            ])
            f.flush()

            display = frame.copy()

            cv2.putText(
                display,
                f"EDGE={edge_st}",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.putText(
                display,
                f"L={final['LEFT']}  C={final['CENTER']}  R={final['RIGHT']}",
                (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,255),
                2
            )

            cv2.imshow("Atlas Live Regression V3", display)
            if cv2.waitKey(1) & 0xFF in (27, ord("q"), ord("Q")):
                break

    finally:
        f.close()
        cap.release()
        cv2.destroyAllWindows()

    match_rate = matches / records if records else 0.0
    unknown_rate = unknown / records if records else 0.0

    print("=" * 92)
    print("LIVE REGRESSION V3 RESULT")
    print("=" * 92)
    print(f"Scenario           : {args.scenario}")
    print(f"Records            : {records}")
    print(f"Matches            : {matches}")
    print(f"Mismatches         : {mismatch}")
    print(f"Match rate         : {match_rate:.3%}")
    print(f"Unknown rate       : {unknown_rate:.3%}")
    print(f"EDGE transitions   : {transitions['EDGE']}")
    print(f"LEFT transitions   : {transitions['LEFT']}")
    print(f"CENTER transitions : {transitions['CENTER']}")
    print(f"RIGHT transitions  : {transitions['RIGHT']}")
    print(f"Results folder     : {out}")
    print("=" * 92)


if __name__ == "__main__":
    main()
