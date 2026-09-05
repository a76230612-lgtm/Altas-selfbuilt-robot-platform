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
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (nw, nh), interpolation=interpolation)

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
        source=image,
        imgsz=IMGSZ,
        device=DEVICE,
        verbose=False
    )[0]
    names = {int(k): str(v).upper() for k, v in r.names.items()}
    ids = {v: k for k, v in names.items()}
    return float(r.probs.data[ids[a]]), float(r.probs.data[ids[b]])


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


def save_jpg(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if ok:
        buf.tofile(str(path))
    return ok


def crop_zone(frame, nav_top, x1r, x2r):
    h, w = frame.shape[:2]
    x1 = int(w * x1r)
    x2 = int(w * x2r)
    y1 = int(h * nav_top)
    return frame[y1:h, x1:x2].copy(), (x1, y1, x2, h)


def crop_edge(frame, roi_top):
    h, w = frame.shape[:2]
    y1 = int(h * roi_top)
    return frame[y1:h, :].copy(), (0, y1, w, h)


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
    release = base / "Atlas_Models" / "RELEASE_CANDIDATES"

    edge_pt = release / "atlas_edge_roi_release.pt"
    edge_js = release / "atlas_edge_roi_release.json"
    dir_pt = release / "atlas_directional_release.pt"
    dir_js = release / "atlas_directional_release.json"

    required = [edge_pt, edge_js, dir_pt, dir_js]
    missing = [x for x in required if not x.exists()]
    if missing:
        print("RELEASE FILE CHECK: FAIL")
        for x in missing:
            print("MISSING:", x)
        sys.exit(1)

    ecfg = load_json(edge_js)
    dcfg = load_json(dir_js)

    edge_t = float(ecfg["threshold"])
    edge_roi_top = float(ecfg["roi_top_ratio"])
    dir_t = float(dcfg["threshold"])
    dir_thresholds = {"LEFT": dir_t, "CENTER": dir_t, "RIGHT": dir_t}

    zone_threshold_json = release / "atlas_directional_zone_thresholds.json"
    if zone_threshold_json.exists():
        zcfg = load_json(zone_threshold_json)
        zt = zcfg.get("thresholds", {})
        for z in ["LEFT", "CENTER", "RIGHT"]:
            if z in zt:
                dir_thresholds[z] = float(zt[z])

    nav_top = float(dcfg["nav_top_ratio"])
    zones = dcfg["zone_ranges"]

    print("=" * 88)
    print("Atlas 6.0 - Camera Live Regression V2 (Zone Thresholds)")
    print("=" * 88)
    print(f"Scenario            : {args.scenario}")
    print(f"Expected EDGE       : {args.edge}")
    print(f"Expected L/C/R      : {args.left}/{args.center}/{args.right}")
    print(f"EDGE threshold      : {edge_t}")
    print(f"Directional base th.: {dir_t}")
    print(f"LEFT threshold      : {dir_thresholds['LEFT']}")
    print(f"CENTER threshold    : {dir_thresholds['CENTER']}")
    print(f"RIGHT threshold     : {dir_thresholds['RIGHT']}")
    print(f"NAV top ratio       : {nav_top}")
    print(f"LEFT range          : {zones['LEFT']}")
    print(f"CENTER range        : {zones['CENTER']}")
    print(f"RIGHT range         : {zones['RIGHT']}")
    print()

    edge_model = YOLO(str(edge_pt))
    dir_model = YOLO(str(dir_pt))

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA CHECK: FAIL")
        sys.exit(2)

    for _ in range(30):
        cap.read()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = base / "Camera_Regression_Results" / f"{args.scenario}_{run_id}"
    mismatch_dir = out / "MISMATCH_FRAMES"
    crops_dir = out / "MISMATCH_CROPS"
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / "regression.csv"
    f = csv_path.open("w", newline="", encoding="utf-8-sig")

    fields = [
        "time",
        "edge_raw", "edge_stable", "edge_p", "safe_p",
        "left_raw", "left_stable", "left_blocked_p", "left_free_p",
        "center_raw", "center_stable", "center_blocked_p", "center_free_p",
        "right_raw", "right_stable", "right_blocked_p", "right_free_p",
        "final_left", "final_center", "final_right",
        "match"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    eh = deque(maxlen=HISTORY_SIZE)
    dh = {z: deque(maxlen=HISTORY_SIZE) for z in ["LEFT", "CENTER", "RIGHT"]}

    raw_e = stable_e = "UNKNOWN"
    raw_d = {z: "UNKNOWN" for z in dh}
    stable_d = {z: "UNKNOWN" for z in dh}

    ep = sp = 0.0
    bp = {z: 0.0 for z in dh}
    fp = {z: 0.0 for z in dh}

    expected = {"LEFT": args.left, "CENTER": args.center, "RIGHT": args.right}

    records = matches = mismatch = unknown_final = 0
    transitions = {z: 0 for z in ["EDGE", "LEFT", "CENTER", "RIGHT"]}
    last_stable = {z: None for z in transitions}

    start = time.time()
    last_infer = 0
    infer_interval = 1 / max(args.inference_fps, 0.5)

    print("Running live regression...")
    print("Do not change the scene during this run.")

    try:
        while time.time() - start < args.seconds:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            now = time.time()
            if now - last_infer < infer_interval:
                cv2.imshow("Atlas Camera Regression", frame)
                cv2.waitKey(1)
                continue

            last_infer = now

            edge_crop, _ = crop_edge(frame, edge_roi_top)
            edge_input = letterbox_square(edge_crop)
            ep, sp = probs_for(edge_model, edge_input, "EDGE", "SAFE")
            raw_e = tri_state(ep, sp, edge_t, "EDGE", "SAFE")
            eh.append(raw_e)
            stable_e = stable(eh, "EDGE", "SAFE")

            crops = {}
            boxes = {}

            for z in ["LEFT", "CENTER", "RIGHT"]:
                x1r, x2r = zones[z]
                crop, box = crop_zone(frame, nav_top, x1r, x2r)
                crops[z] = crop
                boxes[z] = box

                inp = letterbox_square(crop)
                bp[z], fp[z] = probs_for(dir_model, inp, "BLOCKED", "FREE")
                raw_d[z] = tri_state(bp[z], fp[z], dir_thresholds[z], "BLOCKED", "FREE")
                dh[z].append(raw_d[z])
                stable_d[z] = stable(dh[z], "BLOCKED", "FREE")

            if stable_e == "EDGE":
                final = {z: "EDGE" for z in dh}
            elif stable_e == "UNKNOWN":
                final = {z: "UNKNOWN" for z in dh}
            else:
                final = dict(stable_d)

            if last_stable["EDGE"] is not None and stable_e != last_stable["EDGE"]:
                transitions["EDGE"] += 1
            last_stable["EDGE"] = stable_e

            for z in dh:
                if last_stable[z] is not None and stable_d[z] != last_stable[z]:
                    transitions[z] += 1
                last_stable[z] = stable_d[z]

            if stable_e == "UNKNOWN" or any(v == "UNKNOWN" for v in final.values()):
                unknown_final += 1

            is_match = (
                stable_e == args.edge and
                final["LEFT"] == expected["LEFT"] and
                final["CENTER"] == expected["CENTER"] and
                final["RIGHT"] == expected["RIGHT"]
            )

            records += 1
            if is_match:
                matches += 1
            else:
                mismatch += 1
                stamp = datetime.now().strftime("%H%M%S_%f")
                display = frame.copy()

                for z, box in boxes.items():
                    x1, y1, x2, y2 = box
                    cv2.rectangle(display, (x1, y1), (x2 - 1, y2 - 1), (255, 255, 255), 2)
                    cv2.putText(
                        display,
                        f"{z}:{final[z]} B={bp[z]:.2f} F={fp[z]:.2f}",
                        (x1 + 5, y1 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (255, 255, 255), 2
                    )

                cv2.putText(
                    display,
                    f"EDGE:{stable_e} E={ep:.2f} S={sp:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    (255, 255, 255), 2
                )

                save_jpg(mismatch_dir / f"{stamp}.jpg", display)
                for z, c in crops.items():
                    save_jpg(
                        crops_dir / z / f"{stamp}_{z}_{final[z]}.jpg",
                        letterbox_square(c)
                    )

            writer.writerow({
                "time": datetime.now().isoformat(timespec="milliseconds"),
                "edge_raw": raw_e,
                "edge_stable": stable_e,
                "edge_p": f"{ep:.6f}",
                "safe_p": f"{sp:.6f}",
                "left_raw": raw_d["LEFT"],
                "left_stable": stable_d["LEFT"],
                "left_blocked_p": f"{bp['LEFT']:.6f}",
                "left_free_p": f"{fp['LEFT']:.6f}",
                "center_raw": raw_d["CENTER"],
                "center_stable": stable_d["CENTER"],
                "center_blocked_p": f"{bp['CENTER']:.6f}",
                "center_free_p": f"{fp['CENTER']:.6f}",
                "right_raw": raw_d["RIGHT"],
                "right_stable": stable_d["RIGHT"],
                "right_blocked_p": f"{bp['RIGHT']:.6f}",
                "right_free_p": f"{fp['RIGHT']:.6f}",
                "final_left": final["LEFT"],
                "final_center": final["CENTER"],
                "final_right": final["RIGHT"],
                "match": "PASS" if is_match else "FAIL"
            })
            f.flush()

            display = frame.copy()
            for z, box in boxes.items():
                x1, y1, x2, y2 = box
                cv2.rectangle(display, (x1, y1), (x2 - 1, y2 - 1), (255, 255, 255), 2)
                cv2.putText(
                    display,
                    f"{z}:{final[z]}",
                    (x1 + 5, y1 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2
                )

            cv2.putText(
                display,
                f"Scenario={args.scenario} EDGE={stable_e}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (255, 255, 255), 2
            )

            cv2.imshow("Atlas Camera Regression", display)
            if cv2.waitKey(1) & 0xFF in (27, ord("q"), ord("Q")):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        f.close()

    match_rate = matches / records if records else 0.0
    unknown_rate = unknown_final / records if records else 0.0

    summary = [
        "=" * 88,
        "CAMERA LIVE REGRESSION RESULT",
        "=" * 88,
        f"Scenario           : {args.scenario}",
        f"Records            : {records}",
        f"Matches            : {matches}",
        f"Mismatches         : {mismatch}",
        f"Match rate         : {match_rate:.3%}",
        f"Unknown rate       : {unknown_rate:.3%}",
        f"EDGE transitions   : {transitions['EDGE']}",
        f"LEFT transitions   : {transitions['LEFT']}",
        f"CENTER transitions : {transitions['CENTER']}",
        f"RIGHT transitions  : {transitions['RIGHT']}",
        f"Results folder     : {out}",
        "=" * 88,
    ]

    print("\n".join(summary))
    (out / "summary.txt").write_text("\n".join(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
