import argparse
import json
import socket
import sys
import time
from collections import Counter, deque
from pathlib import Path

import cv2
from ultralytics import YOLO

CAMERA_INDEX_DEFAULT = 1
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)
HISTORY_SIZE = 5
MIN_VOTES = 3
DEVICE = "cpu"

ESP32_IP_DEFAULT = "192.168.4.1"
ESP32_PORT_DEFAULT = 8888
INFERENCE_FPS_DEFAULT = 5.0
HEARTBEAT_INTERVAL = 0.10


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
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=PAD_COLOR
    )


def class_probabilities(model, image, class_a, class_b):
    result = model.predict(
        source=image, imgsz=TARGET_SIZE, device=DEVICE, verbose=False
    )[0]
    names = {int(k): str(v).upper() for k, v in result.names.items()}
    name_to_id = {v: k for k, v in names.items()}
    if class_a not in name_to_id or class_b not in name_to_id:
        raise RuntimeError(f"Expected {class_a}/{class_b}, got {result.names}")
    pa = float(result.probs.data[name_to_id[class_a]])
    pb = float(result.probs.data[name_to_id[class_b]])
    return pa, pb


def tri_state(pa, pb, threshold, la, lb):
    if pa >= threshold:
        return la
    if pb >= threshold:
        return lb
    return "UNKNOWN"


def conservative_stable(history, positive_label, negative_label):
    if len(history) < HISTORY_SIZE:
        return "UNKNOWN"
    c = Counter(history)
    if c[positive_label] >= MIN_VOTES:
        return positive_label
    if c[negative_label] >= MIN_VOTES and c[positive_label] == 0:
        return negative_label
    return "UNKNOWN"


def crop_edge_roi(frame, roi_top_ratio):
    h, _ = frame.shape[:2]
    y1 = int(h * roi_top_ratio)
    return frame[y1:h, :].copy()


def crop_direction_zone(frame, nav_top_ratio, x1_ratio, x2_ratio):
    h, w = frame.shape[:2]
    y1 = int(h * nav_top_ratio)
    x1 = int(w * x1_ratio)
    x2 = int(w * x2_ratio)
    return frame[y1:h, x1:x2].copy()


def send_line(sock, text):
    sock.sendall((text + "\n").encode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    ap.add_argument("--ip", default=ESP32_IP_DEFAULT)
    ap.add_argument("--port", type=int, default=ESP32_PORT_DEFAULT)
    ap.add_argument("--inference-fps", type=float, default=INFERENCE_FPS_DEFAULT)
    ap.add_argument(
        "--arm-auto", action="store_true",
        help="DANGEROUS: after bridge is stable, ARM and AUTO ON automatically."
    )
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    release = base / "Atlas_Models" / "RELEASE_CANDIDATES"
    edge_pt = release / "atlas_edge_roi_release.pt"
    edge_json = release / "atlas_edge_roi_release.json"
    dir_pt = release / "atlas_directional_release.pt"
    dir_json = release / "atlas_directional_release.json"

    missing = [p for p in (edge_pt, edge_json, dir_pt, dir_json) if not p.exists()]
    if missing:
        print("RELEASE FILE CHECK: FAIL")
        for p in missing:
            print("  MISSING:", p)
        sys.exit(1)

    ecfg = load_json(edge_json)
    dcfg = load_json(dir_json)
    edge_threshold = float(ecfg["threshold"])
    edge_roi_top = float(ecfg["roi_top_ratio"])
    dir_threshold = float(dcfg["threshold"])
    nav_top_ratio = float(dcfg.get("nav_top_ratio", 0.28))
    zones = dcfg["zone_ranges"]

    print("RELEASE FILE CHECK: PASS")
    print(f"EDGE threshold: {edge_threshold:.2f}")
    print(f"Directional threshold: {dir_threshold:.2f}")
    print("CENTER camera output: intentionally ignored")

    edge_model = YOLO(str(edge_pt))
    dir_model = YOLO(str(dir_pt))
    print("MODELS: PASS")

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA: FAIL")
        sys.exit(2)

    print(f"Connecting to ESP32 {args.ip}:{args.port} ...")
    sock = socket.create_connection((args.ip, args.port), timeout=5.0)
    sock.settimeout(0.05)
    print("ESP32 TCP: PASS")

    # Put controller into fusion mode but do not arm by default.
    send_line(sock, "MODE,FUSION")
    if args.arm_auto:
        print("WARNING: --arm-auto ENABLED")
        send_line(sock, "ARM")
        send_line(sock, "AUTO,ON")
    else:
        print("SAFETY: controller remains DISARMED unless you arm it separately")

    for _ in range(20):
        cap.read()

    histories = {
        "EDGE": deque(maxlen=HISTORY_SIZE),
        "LEFT": deque(maxlen=HISTORY_SIZE),
        "RIGHT": deque(maxlen=HISTORY_SIZE),
    }

    stable_edge = "UNKNOWN"
    stable_left = "UNKNOWN"
    stable_right = "UNKNOWN"
    last_inference = 0.0
    last_hb = 0.0
    interval = 1.0 / max(args.inference_fps, 0.5)

    try:
        while True:
            now = time.monotonic()

            if now - last_hb >= HEARTBEAT_INTERVAL:
                send_line(sock, "HB")
                last_hb = now

            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            if now - last_inference >= interval:
                last_inference = now

                edge_crop = crop_edge_roi(frame, edge_roi_top)
                ep, sp = class_probabilities(
                    edge_model, letterbox_square(edge_crop), "EDGE", "SAFE"
                )
                raw_edge = tri_state(
                    ep, sp, edge_threshold, "EDGE", "SAFE"
                )
                histories["EDGE"].append(raw_edge)
                stable_edge = conservative_stable(
                    histories["EDGE"], "EDGE", "SAFE"
                )

                side_states = {}
                for zone in ("LEFT", "RIGHT"):
                    x1, x2 = zones[zone]
                    crop = crop_direction_zone(frame, nav_top_ratio, x1, x2)
                    bp, fp = class_probabilities(
                        dir_model, letterbox_square(crop), "BLOCKED", "FREE"
                    )
                    raw = tri_state(
                        bp, fp, dir_threshold, "BLOCKED", "FREE"
                    )
                    histories[zone].append(raw)
                    side_states[zone] = conservative_stable(
                        histories[zone], "BLOCKED", "FREE"
                    )

                stable_left = side_states["LEFT"]
                stable_right = side_states["RIGHT"]

                # EDGE goes directly to safety gate.
                if stable_edge == "SAFE":
                    send_line(sock, "CAM,EDGE,SAFE")
                elif stable_edge == "EDGE":
                    send_line(sock, "CAM,EDGE,EDGE")
                else:
                    send_line(sock, "CAM,EDGE,UNKNOWN")

                send_line(sock, f"CAM,LEFT,{stable_left}")
                send_line(sock, f"CAM,RIGHT,{stable_right}")

                print(
                    f"EDGE={stable_edge:<7} "
                    f"LEFT={stable_left:<7} RIGHT={stable_right:<7}",
                    end="\r",
                    flush=True,
                )

            # Consume any ESP32 replies so its TCP buffers do not fill.
            try:
                data = sock.recv(4096)
                if not data:
                    raise ConnectionError("ESP32 closed TCP connection")
            except socket.timeout:
                pass

            # q in camera window isn't used; Ctrl+C is the clean stop.

    except KeyboardInterrupt:
        print("\nStopping bridge...")
        try:
            send_line(sock, "STOP")
            send_line(sock, "DISARM")
        except Exception:
            pass
    finally:
        cap.release()
        try:
            sock.close()
        except Exception:
            pass
        print("Bridge stopped. STOP/DISARM requested.")


if __name__ == "__main__":
    main()
