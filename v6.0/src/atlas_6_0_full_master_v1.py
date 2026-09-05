import argparse
import json
import socket
import sys
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np

import cv2
from ultralytics import YOLO

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from scipy.io.wavfile import write as write_wav
except ImportError:
    write_wav = None

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

VOICE_SAMPLE_RATE = 16000
VOICE_RECORD_SECONDS = 5
NAV_WARNING_COOLDOWN = 1.5


# Strict cliff-safety policy:
# - SAFE is entered only after several consecutive strong SAFE frames.
# - One weak/not-safe frame immediately removes SAFE permission.
# - A confident EDGE frame is reported as EDGE immediately.
SAFE_CONFIRM_FRAMES = 4
MIN_DIAGNOSTIC_SEPARATION = 0.10
SAFE_MARGIN_FRACTION = 0.70
MIN_SAFE_THRESHOLD = 0.80
MAX_SAFE_THRESHOLD = 0.995



# ============================================================
# Atlas 5.0 Interaction + Atlas 6.0 Expression Integration
# ============================================================

class AtlasState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SUCCESS = "SUCCESS"
    ENCOURAGE = "ENCOURAGE"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DialogueIntent(Enum):
    GREETING = "GREETING"
    SELF_INTRO = "SELF_INTRO"
    ENCOURAGEMENT = "ENCOURAGEMENT"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STATUS = "STATUS"
    CAMERA = "CAMERA"
    NORMAL = "NORMAL"


class AtlasVoiceInput:
    @property
    def available(self):
        return sd is not None and sr is not None and write_wav is not None

    def record_and_recognize(self, language="en-US", seconds=VOICE_RECORD_SECONDS):
        if not self.available:
            raise RuntimeError(
                "Voice dependencies missing. Install: "
                "sounddevice scipy SpeechRecognition numpy"
            )

        print(f"\nVOICE RECORDING: {seconds} seconds")
        print("Speak now...")

        audio_data = sd.rec(
            int(seconds * VOICE_SAMPLE_RATE),
            samplerate=VOICE_SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wav_path = temp_file.name
        temp_file.close()

        write_wav(wav_path, VOICE_SAMPLE_RATE, np.asarray(audio_data))

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio, language=language)
            return text, wav_path
        except sr.UnknownValueError:
            return "", wav_path
        except sr.RequestError as exc:
            raise RuntimeError(
                "Google Speech Recognition is unreachable. "
                "Keep PC Wi-Fi on ATLAS_6_0 and provide Internet through "
                "Ethernet or phone USB tethering. "
                f"Details: {exc}"
            )


class AtlasVoiceOutput:
    @property
    def available(self):
        return pyttsx3 is not None

    def speak(self, text):
        if not text:
            return

        print("\nATLAS SAYS:")
        print(text)

        if pyttsx3 is None:
            print("TTS unavailable: pyttsx3 is not installed.")
            return

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()


class AtlasBrain:
    def __init__(self, sock):
        self.sock = sock
        self.state = AtlasState.IDLE

    def set_state(self, state, source="BRAIN"):
        if isinstance(state, str):
            state = AtlasState[state.upper()]

        self.state = state
        send_line(self.sock, f"STATE,{state.value}")
        print(f"\nBRAIN -> {state.value} [{source}]")

    def classify(self, user_text):
        text = user_text.strip().lower()

        if not text:
            return DialogueIntent.ERROR

        if text in ("hello", "hi", "hey", "hello atlas", "你好", "嗨"):
            return DialogueIntent.GREETING

        if (
            "who are you" in text
            or "what are you" in text
            or "what can you do" in text
            or "你是谁" in text
            or "你能做什么" in text
        ):
            return DialogueIntent.SELF_INTRO

        if (
            "encourage" in text
            or "tired" in text
            or "sad" in text
            or "stressed" in text
            or "鼓励" in text
            or "累" in text
            or "压力" in text
            or "难过" in text
        ):
            return DialogueIntent.ENCOURAGEMENT

        if (
            "warning" in text
            or "danger" in text
            or "careful" in text
            or "警告" in text
            or "危险" in text
            or "小心" in text
        ):
            return DialogueIntent.WARNING

        if (
            "error" in text
            or "failed" in text
            or "failure" in text
            or "bug" in text
            or "错误" in text
            or "失败" in text
            or "报错" in text
        ):
            return DialogueIntent.ERROR

        if "status" in text or "状态" in text:
            return DialogueIntent.STATUS

        if (
            "camera" in text
            or "vision" in text
            or "see" in text
            or "摄像头" in text
            or "视觉" in text
            or "看见" in text
        ):
            return DialogueIntent.CAMERA

        return DialogueIntent.NORMAL

    def reply_for(self, intent):
        if intent == DialogueIntent.GREETING:
            return (
                AtlasState.SUCCESS,
                "Hello Eric. I am Atlas 6.0. My voice, vision, expression, "
                "edge safety, and autonomous tabletop navigation are running together.",
            )

        if intent == DialogueIntent.SELF_INTRO:
            return (
                AtlasState.SUCCESS,
                "I am Atlas 6.0, a tabletop robot prototype. "
                "I can listen, speak, show behavior states, move my head, "
                "avoid obstacles, and protect myself from table edges.",
            )

        if intent == DialogueIntent.ENCOURAGEMENT:
            return (
                AtlasState.ENCOURAGE,
                "Keep going. The system is working as one integrated robot now.",
            )

        if intent == DialogueIntent.WARNING:
            return AtlasState.WARNING, "Warning state confirmed."

        if intent == DialogueIntent.ERROR:
            return (
                AtlasState.ERROR,
                "Error state confirmed. Stop the system and inspect one subsystem at a time.",
            )

        if intent == DialogueIntent.STATUS:
            return (
                AtlasState.SUCCESS,
                "Atlas 6.0 is connected through Wi-Fi. "
                "Strict edge safety, US-100 obstacle avoidance, "
                "OLED, RGB expression, and pan tilt behavior are enabled.",
            )

        if intent == DialogueIntent.CAMERA:
            return (
                AtlasState.SUCCESS,
                "The C950 camera is active. The lower image region is being used for edge safety.",
            )

        return (
            AtlasState.SUCCESS,
            "I heard you. Atlas 6.0 is currently using the stable rule based dialogue system.",
        )


def append_master_log(base_dir, title, content):
    path = base_dir / "atlas_6_0_full_master_log.txt"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write(f"{title}\n")
        f.write(f"Time: {stamp}\n")
        f.write("=" * 70 + "\n")
        f.write(str(content) + "\n")
    return path


def save_snapshot(base_dir, frame):
    if frame is None:
        print("SNAPSHOT: FAIL - no frame")
        return ""

    folder = base_dir / "atlas_6_0_snapshots"
    folder.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = folder / f"atlas_6_0_{stamp}.jpg"

    if cv2.imwrite(str(path), frame):
        print("SNAPSHOT: PASS ->", path)
        return str(path)

    print("SNAPSHOT: FAIL")
    return ""


def safe_dialogue(
    sock,
    brain,
    voice_input,
    voice_output,
    base_dir,
    language=None,
    typed=False,
):
    """
    Interaction mode is deliberately motion-safe:
      AUTO OFF -> STOP -> DISARM
      LISTENING -> THINKING -> final behavior -> IDLE

    Navigation must be manually resumed with A then U after the dialogue.
    """
    print("\n" + "=" * 72)
    print("ATLAS SAFE INTERACTION MODE")
    print("=" * 72)

    send_line(sock, "AUTO,OFF")
    send_line(sock, "STOP")
    send_line(sock, "DISARM")

    brain.set_state(AtlasState.LISTENING, "DIALOGUE")

    try:
        if typed:
            user_text = input("TYPE TO ATLAS > ").strip()
            wav_path = ""
            language_name = "Typed"
        else:
            language_code = language or "en-US"
            language_name = "English" if language_code == "en-US" else "Chinese"
            user_text, wav_path = voice_input.record_and_recognize(
                language=language_code
            )
            print(f"VOICE WAV: {wav_path}")
            print(f"VOICE RECOGNIZED: {user_text or '[NOT RECOGNIZED]'}")

        brain.set_state(AtlasState.THINKING, "DIALOGUE")
        time.sleep(0.15)

        intent = brain.classify(user_text)
        final_state, reply = brain.reply_for(intent)

        brain.set_state(final_state, "DIALOGUE")
        voice_output.speak(reply)

        append_master_log(
            base_dir,
            "Atlas 6.0 Dialogue",
            (
                f"language={language_name}\n"
                f"user_text={user_text}\n"
                f"intent={intent.value}\n"
                f"state={final_state.value}\n"
                f"reply={reply}"
            ),
        )

        time.sleep(0.25)
        brain.set_state(AtlasState.IDLE, "DIALOGUE_COMPLETE")

    except Exception as exc:
        print("DIALOGUE ERROR:", exc)
        try:
            brain.set_state(AtlasState.ERROR, "DIALOGUE_ERROR")
        except Exception:
            pass
        append_master_log(base_dir, "Atlas 6.0 Dialogue Error", str(exc))

    print()
    print("Interaction complete.")
    print("Navigation remains STOPPED / DISARMED.")
    print("Wait until EDGE is stable SAFE, then press A followed by U.")
    print("=" * 72)


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
    print("========== Atlas 6.0 Full Master Controls ==========")
    print("Navigation:")
    print("  A = ARM")
    print("  U = AUTO ON")
    print("  O = AUTO OFF")
    print("  X = STOP + DISARM")
    print("  S = STATUS")
    print("  7 = PWM 70")
    print("  1 = PWM 100")
    print()
    print("Behavior hardware:")
    print("  I = IDLE")
    print("  L = LISTENING")
    print("  T = THINKING")
    print("  G = SUCCESS")
    print("  E = ENCOURAGE")
    print("  W = WARNING")
    print("  R = ERROR")
    print()
    print("Interaction:")
    print("  V = English voice dialogue")
    print("  C = Chinese voice dialogue")
    print("  K = typed dialogue fallback")
    print("  P = save current C950 snapshot")
    print()
    print("  Q = SAFE QUIT")
    print("====================================================")
    print()


def handle_keyboard(
    sock,
    brain,
    voice_input,
    voice_output,
    base_dir,
    latest_frame,
):
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
        brain.set_state(AtlasState.IDLE, "USER_STOP")
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

    elif key == "i":
        brain.set_state(AtlasState.IDLE, "MANUAL")

    elif key == "l":
        brain.set_state(AtlasState.LISTENING, "MANUAL")

    elif key == "t":
        brain.set_state(AtlasState.THINKING, "MANUAL")

    elif key == "g":
        brain.set_state(AtlasState.SUCCESS, "MANUAL")

    elif key == "e":
        brain.set_state(AtlasState.ENCOURAGE, "MANUAL")

    elif key == "w":
        brain.set_state(AtlasState.WARNING, "MANUAL")

    elif key == "r":
        brain.set_state(AtlasState.ERROR, "MANUAL")

    elif key == "v":
        safe_dialogue(
            sock, brain, voice_input, voice_output, base_dir,
            language="en-US", typed=False
        )

    elif key == "c":
        safe_dialogue(
            sock, brain, voice_input, voice_output, base_dir,
            language="zh-CN", typed=False
        )

    elif key == "k":
        safe_dialogue(
            sock, brain, voice_input, voice_output, base_dir,
            typed=True
        )

    elif key == "p":
        save_snapshot(base_dir, latest_frame)

    elif key == "q":
        print("\nKEYBOARD -> SAFE QUIT")
        return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Atlas 6.0 Full Master: strict EDGE + navigation + 5.0 voice/expression."
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

    brain = AtlasBrain(sock)
    voice_input = AtlasVoiceInput()
    voice_output = AtlasVoiceOutput()

    print()
    print("FULL MASTER:")
    print("  V3.5.2 expression commands -> ENABLED")
    print("  English/Chinese voice       -> " + ("AVAILABLE" if voice_input.available else "DEPENDENCY MISSING"))
    print("  Local pyttsx3 TTS           -> " + ("AVAILABLE" if voice_output.available else "DEPENDENCY MISSING"))
    print("  C950 camera                 -> ONE shared camera instance")
    print("  Old USB Serial HAL          -> DISABLED")
    print()

    # Enter fusion mode, but remain DISARMED.
    send_line(sock, "MODE,FUSION")
    send_line(sock, "CAM,EDGE,UNKNOWN")
    send_line(sock, "CAM,LEFT,UNKNOWN")
    send_line(sock, "CAM,RIGHT,UNKNOWN")
    send_line(sock, "STATUS")
    brain.set_state(AtlasState.IDLE, "BOOT")

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
    latest_frame = None
    rx_buffer = ""
    last_warning_state = 0.0

    try:
        while True:
            now = time.monotonic()

            if handle_keyboard(
                sock,
                brain,
                voice_input,
                voice_output,
                base,
                latest_frame,
            ):
                break

            if now - last_hb >= HEARTBEAT_INTERVAL:
                send_line(sock, "HB")
                last_hb = now

            if now - last_status_request >= STATUS_REQUEST_INTERVAL:
                send_line(sock, "STATUS")
                last_status_request = now

            ok, frame = cap.read()

            if ok and frame is not None:
                latest_frame = frame.copy()
                preview = frame.copy()
                cv2.putText(
                    preview,
                    f"EDGE: {stable_edge}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    preview,
                    f"STATE: {brain.state.value}",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow("Atlas 6.0 Full Master - C950", preview)
                cv2.waitKey(1)

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
                    or line.startswith("HEAD,")
                ):
                    latest_event = line

                hazard_event = (
                    "CAMERA_EDGE" in line
                    or "CENTER_BLOCKED" in line
                    or "CENTER_CAUTION" in line
                    or "BACKOFF" in line
                    or "RECOVERY_NO_SAFE_TURN" in line
                )

                if hazard_event and now - last_warning_state >= NAV_WARNING_COOLDOWN:
                    brain.set_state(AtlasState.WARNING, "NAVIGATION")
                    last_warning_state = now

                elif line.startswith("AUTO,ACTION,FORWARD"):
                    if brain.state == AtlasState.WARNING:
                        brain.set_state(AtlasState.IDLE, "NAVIGATION_CLEAR")

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
                print(f"BRAIN| STATE={brain.state.value}")
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
        cv2.destroyAllWindows()

        try:
            sock.close()
        except Exception:
            pass

        print("Console stopped. STOP/DISARM requested.")


if __name__ == "__main__":
    main()
