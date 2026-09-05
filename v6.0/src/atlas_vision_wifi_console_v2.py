import argparse
import json
import os
import socket
import sys
import time
from collections import Counter, deque
from pathlib import Path

import cv2
from ultralytics import YOLO

try:
    import msvcrt  # Windows non-blocking keyboard input
except ImportError:
    msvcrt = None

CAMERA_INDEX_DEFAULT = 0
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
STATUS_REQUEST_INTERVAL = 1.0
CONSOLE_REFRESH_INTERVAL = 0.50


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
        source=image,
        imgsz=TARGET_SIZE,
        device=DEVICE,
        verbose=False,
    )[0]
    names = {int(k): str(v).upper() for k, v in result.names.items()}
    name_to_id = {v: k for k, v in names.items()}
    if class_a not in name_to_id or class_b not in name_to_id:
        raise RuntimeError(f"Expected {class_a}/{class_b}, got {result.names}")
    pa = float(result.probs.data[name_to_id[class_a]])
    pb = float(result.probs.data[name_to_id[class_b]])
    return pa, pb


def tri_state(pa, pb, threshold, label_a, label_b):
    if pa >= threshold:
        return label_a
    if pb >= threshold:
        return label_b
    return "UNKNOWN"


def conservative_stable(history, positive_label, negative_label):
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
    return frame[y1:h, :].copy()


def crop_direction_zone(frame, nav_top_ratio, x1_ratio, x2_ratio):
    h, w = frame.shape[:2]
    y1 = int(h * nav_top_ratio)
    x1 = int(w * x1_ratio)
    x2 = int(w * x2_ratio)
    return frame[y1:h, x1:x2].copy()


def send_line(sock, text):
    sock.sendall((text + "\n").encode("utf-8"))


def print_controls():
    print()
    print("Keyboard controls (PowerShell window focused):")
    print("  A = ARM")
    print("  U = AUTO ON")
    print("  O = AUTO OFF")
    print("  X = STOP + DISARM")
    print("  S = request STATUS")
    print("  Q = safe quit")
    print()


def handle_keyboard(sock):
    if msvcrt is None or not msvcrt.kbhit():
        return False

    key = msvcrt.getwch().lower()

    if key == "a":
        send_line(sock, "ARM")
        print("\nKEYBOARD -> ARM")
    elif key == "u":
        send_line(sock, "AUTO,ON")
        print("\nKEYBOARD -> AUTO ON")
    elif key == "o":
        send_line(sock, "AUTO,OFF")
        print("\nKEYBOARD -> AUTO OFF")
    elif key == "x":
        send_line(sock, "STOP")
        send_line(sock, "DISARM")
        print("\nKEYBOARD -> STOP + DISARM")
    elif key == "s":
        send_line(sock, "STATUS")
        print("\nKEYBOARD -> STATUS")
    elif key == "q":
        print("\nKEYBOARD -> SAFE QUIT")
        return True

    return False


def parse_rx_lines(sock, rx_buffer):
    events = []
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                raise ConnectionError("ESP32 closed TCP connection")
            rx_buffer += data.decode("utf-8", errors="replace")
        except socket.timeout:
            break
        except BlockingIOError:
            break

    while "\n" in rx_buffer:
        line, rx_buffer = rx_buffer.split("\n", 1)
        line = line.strip()
        if line:
            events.append(line)

    return rx_buffer, events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    parser.add_argument("--ip", default=ESP32_IP_DEFAULT)
    parser.add_argument("--port", type=int, default=ESP32_PORT_DEFAULT)
    parser.add_argument("--inference-fps", type=float, default=INFERENCE_FPS_DEFAULT)
    parser.add_argument(
        "--arm-auto",
        action="store_true",
        help="After bridge is stable, automatically ARM and AUTO ON.",
    )
    args = parser.parse_args()

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

    edge_cfg = load_json(edge_json)
    dir_cfg = load_json(dir_json)

    edge_threshold = float(edge_cfg["threshold"])
    edge_roi_top = float(edge_cfg["roi_top_ratio"])
    dir_threshold = float(dir_cfg["threshold"])
    nav_top_ratio = float(dir_cfg.get("nav_top_ratio", 0.28))
    zones = dir_cfg["zone_ranges"]

    print("RELEASE FILE CHECK: PASS")
    print(f"EDGE threshold: {edge_threshold:.2f}")
    print(f"Directional threshold: {dir_threshold:.2f}")
    print("CENTER camera output: intentionally ignored")
    print("LEFT/RIGHT UNKNOWN is neutral; US-100 remains physical authority")

    edge_model = YOLO(str(edge_pt))
    dir_model = YOLO(str(dir_pt))
    print("MODELS: PASS")

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA: FAIL")
        sys.exit(2)

    print(f"Connecting to ESP32 {args.ip}:{args.port} ...")
    sock = socket.create_connection((args.ip, args.port), timeout=5.0)
    sock.settimeout(0.01)
    print("ESP32 TCP: PASS")

    # Enter fusion mode. Do not arm unless explicitly requested.
    send_line(sock, "MODE,FUSION")
    send_line(sock, "STATUS")

    if args.arm_auto:
        print("WARNING: --arm-auto ENABLED")
        send_line(sock, "ARM")
        send_line(sock, "AUTO,ON")
    else:
        print("SAFETY: controller remains DISARMED until you press A")

    print_controls()

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
    last_status_request = 0.0
    last_console = 0.0
    interval = 1.0 / max(args.inference_fps, 0.5)

    latest_status = "STATUS,WAITING"
    latest_event = ""
    rx_buffer = ""

    try:
        while True:
            now = time.monotonic()

            if handle_keyboard(sock):
                break

            if now - last_hb >= HEARTBEAT_INTERVAL:
                send_line(sock, "HB")
                last_hb = now

            if now - last_status_request >= STATUS_REQUEST_INTERVAL:
                send_line(sock, "STATUS")
                last_status_request = now

            ok, frame = cap.read()
            if ok and frame is not None and now - last_inference >= interval:
                last_inference = now

                edge_crop = crop_edge_roi(frame, edge_roi_top)
                edge_p, safe_p = class_probabilities(
                    edge_model,
                    letterbox_square(edge_crop),
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
                    "EDGE",
                    "SAFE",
                )

                side_states = {}
                for zone in ("LEFT", "RIGHT"):
                    x1, x2 = zones[zone]
                    crop = crop_direction_zone(
                        frame,
                        nav_top_ratio,
                        x1,
                        x2,
                    )
                    blocked_p, free_p = class_probabilities(
                        dir_model,
                        letterbox_square(crop),
                        "BLOCKED",
                        "FREE",
                    )
                    raw_side = tri_state(
                        blocked_p,
                        free_p,
                        dir_threshold,
                        "BLOCKED",
                        "FREE",
                    )
                    histories[zone].append(raw_side)
                    side_states[zone] = conservative_stable(
                        histories[zone],
                        "BLOCKED",
                        "FREE",
                    )

                stable_left = side_states["LEFT"]
                stable_right = side_states["RIGHT"]

                # EDGE is the safety gate.
                if stable_edge == "SAFE":
                    send_line(sock, "CAM,EDGE,SAFE")
                elif stable_edge == "EDGE":
                    send_line(sock, "CAM,EDGE,EDGE")
                else:
                    send_line(sock, "CAM,EDGE,UNKNOWN")

                # LEFT/RIGHT are only hints. UNKNOWN is intentionally preserved.
                send_line(sock, f"CAM,LEFT,{stable_left}")
                send_line(sock, f"CAM,RIGHT,{stable_right}")

            rx_buffer, events = parse_rx_lines(sock, rx_buffer)
            for line in events:
                if line.startswith("STATUS,"):
                    latest_status = line
                elif line.startswith("ERROR,") or line.startswith("MOTION,") or line.startswith("AUTO,ACTION,"):
                    latest_event = line
                elif line.startswith("ACK,"):
                    latest_event = line

            if now - last_console >= CONSOLE_REFRESH_INTERVAL:
                last_console = now
                print()
                print(
                    f"CAM | EDGE={stable_edge:<7} LEFT={stable_left:<7} RIGHT={stable_right:<7}"
                )
                print(f"ESP | {latest_status}")
                if latest_event:
                    print(f"EVT | {latest_event}")

    except KeyboardInterrupt:
        print("\nCtrl+C received.")
    except Exception as exc:
        print(f"\nERROR: {exc}")
    finally:
        try:
            send_line(sock, "STOP")
            send_line(sock, "DISARM")
        except Exception:
            pass
        cap.release()
        try:
            sock.close()
        except Exception:
            pass
        print("Bridge stopped. STOP/DISARM requested.")


if __name__ == "__main__":
    main()
