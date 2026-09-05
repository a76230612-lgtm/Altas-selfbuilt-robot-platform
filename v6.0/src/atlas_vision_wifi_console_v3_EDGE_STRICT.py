import argparse
import json
import socket
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

try:
    import msvcrt
except ImportError:
    msvcrt = None

CAMERA_INDEX_DEFAULT = 1
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)
DEVICE = "cpu"

ESP32_IP_DEFAULT = "192.168.4.1"
ESP32_PORT_DEFAULT = 8888
INFERENCE_FPS_DEFAULT = 5.0
HEARTBEAT_INTERVAL = 0.10
STATUS_REQUEST_INTERVAL = 1.0
CONSOLE_REFRESH_INTERVAL = 0.50

# Strict cliff-safety policy:
# - SAFE is entered only after several consecutive strong SAFE frames.
# - One weak/not-safe frame immediately removes SAFE permission.
# - A confident EDGE frame is reported as EDGE immediately.
SAFE_CONFIRM_FRAMES = 4
MIN_DIAGNOSTIC_SEPARATION = 0.10
SAFE_MARGIN_FRACTION = 0.70
MIN_SAFE_THRESHOLD = 0.80
MAX_SAFE_THRESHOLD = 0.995


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


def send_line(sock, text):
    sock.sendall((text + "\n").encode("utf-8"))


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


def calculate_strict_safe_threshold(base: Path, configured_threshold: float):
    diag = base / "edge_diagnostic"
    safe_path = diag / "safe_summary.json"
    edge_path = diag / "edge_summary.json"

    if not safe_path.exists() or not edge_path.exists():
        raise RuntimeError(
            "Missing edge_diagnostic/safe_summary.json or edge_summary.json. "
            "Run atlas_edge_safety_diagnostic_v1.py for SAFE and EDGE first."
        )

    safe = load_json(safe_path)
    edge = load_json(edge_path)

    safe_floor = float(safe["p_safe"]["p05"])
    edge_safe_ceiling = float(edge["p_safe"]["p95"])
    separation = safe_floor - edge_safe_ceiling

    if separation < MIN_DIAGNOSTIC_SEPARATION:
        raise RuntimeError(
            f"Diagnostic separation too small ({separation:.3f}). "
            "Do not use threshold-only fix; retrain EDGE model."
        )

    # Conservative threshold: 70% of the way from EDGE ceiling toward SAFE floor.
    strict_threshold = edge_safe_ceiling + SAFE_MARGIN_FRACTION * separation
    strict_threshold = max(configured_threshold, strict_threshold, MIN_SAFE_THRESHOLD)
    strict_threshold = min(strict_threshold, MAX_SAFE_THRESHOLD)

    # Never set the threshold above the measured SAFE p05.
    # Leave a small operating margin for normal SAFE variation.
    if strict_threshold >= safe_floor:
        strict_threshold = max(
            configured_threshold,
            min(MAX_SAFE_THRESHOLD, safe_floor - 0.01),
        )

    return strict_threshold, safe_floor, edge_safe_ceiling, separation


def print_controls():
    print()
    print("Keyboard controls (PowerShell focused):")
    print("  A = ARM")
    print("  U = AUTO ON")
    print("  O = AUTO OFF")
    print("  X = STOP + DISARM")
    print("  S = request STATUS")
    print("  7 = PWM 70 (low-speed ground safety test)")
    print("  1 = PWM 100 (normal cruise)")
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
    elif key == "7":
        send_line(sock, "PWM,70")
        print("\nKEYBOARD -> PWM 70")
    elif key == "1":
        send_line(sock, "PWM,100")
        print("\nKEYBOARD -> PWM 100")
    elif key == "q":
        print("\nKEYBOARD -> SAFE QUIT")
        return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Atlas 6.0 strict EDGE-safe Wi-Fi console."
    )
    parser.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    parser.add_argument("--ip", default=ESP32_IP_DEFAULT)
    parser.add_argument("--port", type=int, default=ESP32_PORT_DEFAULT)
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

    edge_cfg = load_json(edge_json)
    configured_threshold = float(edge_cfg["threshold"])
    edge_roi_top = float(edge_cfg["roi_top_ratio"])

    try:
        strict_safe_threshold, safe_floor, edge_safe_ceiling, separation = (
            calculate_strict_safe_threshold(base, configured_threshold)
        )
    except Exception as exc:
        print("EDGE SAFETY CALIBRATION: FAIL")
        print("  ", exc)
        sys.exit(2)

    print("RELEASE FILE CHECK: PASS")
    print("EDGE SAFETY CALIBRATION: PASS")
    print(f"Original model threshold       : {configured_threshold:.3f}")
    print(f"Measured SAFE P_SAFE p05       : {safe_floor:.3f}")
    print(f"Measured EDGE-scene P_SAFE p95 : {edge_safe_ceiling:.3f}")
    print(f"Diagnostic separation          : {separation:.3f}")
    print(f"STRICT SAFE threshold          : {strict_safe_threshold:.3f}")
    print(f"SAFE confirmation frames       : {SAFE_CONFIRM_FRAMES}")
    print()
    print("POLICY:")
    print("  EDGE confident       -> immediate CAM,EDGE,EDGE")
    print("  SAFE below strict min-> immediate CAM,EDGE,UNKNOWN")
    print("  Strong SAFE          -> must persist for consecutive frames")
    print("  LEFT/RIGHT camera    -> DISABLED for navigation")
    print("  US-100               -> sole LEFT/RIGHT physical authority")
    print()

    edge_model = YOLO(str(edge_pt))
    print("EDGE MODEL: PASS")

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA: FAIL")
        sys.exit(3)

    print(f"Connecting to ESP32 {args.ip}:{args.port} ...")
    sock = socket.create_connection((args.ip, args.port), timeout=5.0)
    sock.settimeout(0.01)
    print("ESP32 TCP: PASS")

    # Enter fusion mode, but remain DISARMED.
    send_line(sock, "MODE,FUSION")
    send_line(sock, "CAM,EDGE,UNKNOWN")
    send_line(sock, "CAM,LEFT,UNKNOWN")
    send_line(sock, "CAM,RIGHT,UNKNOWN")
    send_line(sock, "STATUS")

    print("SAFETY: controller remains DISARMED until you press A")
    print_controls()

    for _ in range(20):
        cap.read()

    interval = 1.0 / max(args.inference_fps, 0.5)
    last_inference = 0.0
    last_hb = 0.0
    last_status_request = 0.0
    last_console = 0.0

    safe_streak = 0
    stable_edge = "UNKNOWN"
    latest_p_edge = 0.0
    latest_p_safe = 0.0

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
                p_edge, p_safe = edge_probabilities(
                    edge_model,
                    letterbox_square(edge_crop),
                )

                latest_p_edge = p_edge
                latest_p_safe = p_safe

                # Fail-safe state machine:
                # 1) Confident EDGE -> EDGE immediately.
                # 2) Anything not strongly SAFE -> UNKNOWN immediately.
                # 3) Strong SAFE requires consecutive confirmation.
                if p_edge >= configured_threshold:
                    safe_streak = 0
                    stable_edge = "EDGE"
                elif p_safe < strict_safe_threshold:
                    safe_streak = 0
                    stable_edge = "UNKNOWN"
                else:
                    safe_streak += 1
                    if safe_streak >= SAFE_CONFIRM_FRAMES:
                        stable_edge = "SAFE"
                    else:
                        stable_edge = "UNKNOWN"

                if stable_edge == "SAFE":
                    send_line(sock, "CAM,EDGE,SAFE")
                elif stable_edge == "EDGE":
                    send_line(sock, "CAM,EDGE,EDGE")
                else:
                    send_line(sock, "CAM,EDGE,UNKNOWN")

                # Directional camera is deliberately removed from navigation.
                # Send UNKNOWN so V3.3 treats both sides neutrally and US-100 decides.
                send_line(sock, "CAM,LEFT,UNKNOWN")
                send_line(sock, "CAM,RIGHT,UNKNOWN")

            rx_buffer, events = parse_rx_lines(sock, rx_buffer)

            for line in events:
                if line.startswith("STATUS,"):
                    latest_status = line
                elif (
                    line.startswith("ERROR,")
                    or line.startswith("MOTION,")
                    or line.startswith("AUTO,ACTION,")
                    or line.startswith("ACK,")
                ):
                    latest_event = line

            if now - last_console >= CONSOLE_REFRESH_INTERVAL:
                last_console = now
                print()
                print(
                    f"EDGE | STATE={stable_edge:<7} "
                    f"P_EDGE={latest_p_edge:.3f} "
                    f"P_SAFE={latest_p_safe:.3f} "
                    f"SAFE_STREAK={safe_streak}/{SAFE_CONFIRM_FRAMES}"
                )
                print("SIDE | LEFT=UNKNOWN RIGHT=UNKNOWN (camera hints disabled)")
                print(f"ESP  | {latest_status}")
                if latest_event:
                    print(f"EVT  | {latest_event}")

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

        print("Console stopped. STOP/DISARM requested.")


if __name__ == "__main__":
    main()
