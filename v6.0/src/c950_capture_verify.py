import cv2
import time
import sys
from pathlib import Path
from datetime import datetime

CAMERA_INDEX = 1
SAVE_COUNT = 5
SAVE_INTERVAL_SECONDS = 1.0
WARMUP_FRAMES = 30


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
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        ok, frame = cap.read()
        if ok and frame is not None:
            print(f"Camera opened with backend: {name}")
            return cap

        cap.release()

    return None


def save_jpeg_unicode_safe(path: Path, frame) -> bool:
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        return False

    try:
        encoded.tofile(str(path))
    except Exception as exc:
        print(f"WRITE EXCEPTION: {exc}")
        return False

    return path.exists() and path.stat().st_size > 0


def main():
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir / "C950_CAPTURE_TEST"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Atlas 6.0 - EMEET C950 Capture Verification")
    print("=" * 70)
    print(f"Python executable : {sys.executable}")
    print(f"Camera index      : {CAMERA_INDEX}")
    print(f"Absolute save dir : {output_dir}")
    print()

    probe = output_dir / "_write_test.tmp"
    try:
        probe.write_text("write test", encoding="utf-8")
        if not probe.exists():
            raise RuntimeError("probe file was not created")
        probe.unlink()
        print("Folder write test : PASS")
    except Exception as exc:
        print("Folder write test : FAIL")
        print(f"Reason            : {exc}")
        sys.exit(1)

    cap = open_camera(CAMERA_INDEX)
    if cap is None:
        print("Camera open       : FAIL")
        print("Check that Windows Camera/Teams/Zoom/browser is not using the C950.")
        sys.exit(2)

    print("Camera open       : PASS")

    try:
        print(f"Warming up camera for {WARMUP_FRAMES} frames...")
        for _ in range(WARMUP_FRAMES):
            ok, _ = cap.read()
            if not ok:
                time.sleep(0.03)

        saved = 0

        for i in range(1, SAVE_COUNT + 1):
            ok, frame = cap.read()

            if not ok or frame is None:
                print(f"[{i}/{SAVE_COUNT}] Frame read: FAIL")
                time.sleep(SAVE_INTERVAL_SECONDS)
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = output_dir / f"C950_RAW_{i:02d}_{timestamp}.jpg"

            saved_ok = save_jpeg_unicode_safe(path, frame)

            if saved_ok:
                saved += 1
                print(f"[{i}/{SAVE_COUNT}] SAVE PASS | {path.name} | {path.stat().st_size} bytes")
            else:
                print(f"[{i}/{SAVE_COUNT}] SAVE FAIL | {path}")

            time.sleep(SAVE_INTERVAL_SECONDS)

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Saved images      : {saved}/{SAVE_COUNT}")
    print(f"Open this folder  : {output_dir}")

    if saved == SAVE_COUNT:
        print("CAPTURE TEST      : PASS")
        print()
        print("Use any C950_RAW_*.jpg file for the Ultralytics inference test.")
        sys.exit(0)

    print("CAPTURE TEST      : FAIL")
    sys.exit(3)


if __name__ == "__main__":
    main()
