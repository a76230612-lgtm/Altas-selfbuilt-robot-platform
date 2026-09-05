import cv2
import time
from pathlib import Path
from datetime import datetime


# ============================================================
# Atlas 6.0 - C950 Vision Baseline
#
# Purpose:
# 1. Verify that the EMEET C950 can provide a stable video feed.
# 2. Measure actual FPS.
# 3. Display LEFT / CENTER / RIGHT visual regions.
# 4. Save test frames manually.
#
# This program DOES NOT:
# - control Atlas
# - control ESP32
# - perform obstacle avoidance
# - perform AI classification
# ============================================================


CAMERA_INDEX = 1

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
TARGET_FPS = 30

TEST_DURATION_SECONDS = 600  # 10 minutes

OUTPUT_DIR = Path("frames")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def open_camera(index: int):
    camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not camera.isOpened():
        return None

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    return camera


def main():
    print("=" * 60)
    print("Atlas 6.0 - EMEET C950 Vision Baseline")
    print("=" * 60)
    print(f"Trying camera index: {CAMERA_INDEX}")

    cap = open_camera(CAMERA_INDEX)

    if cap is None:
        print()
        print("ERROR: Camera could not be opened.")
        print("Try CAMERA_INDEX = 1, then 2, then 3.")
        return

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    reported_fps = cap.get(cv2.CAP_PROP_FPS)

    print()
    print("Camera opened successfully.")
    print(f"Actual resolution : {actual_width} x {actual_height}")
    print(f"Reported FPS      : {reported_fps:.2f}")
    print()
    print("Controls:")
    print("  S = save current frame")
    print("  Q = quit")
    print()

    start_time = time.time()
    fps_window_start = time.time()

    frame_counter = 0
    fps_window_frames = 0
    measured_fps = 0.0

    read_failures = 0
    saved_frames = 0

    while True:
        success, frame = cap.read()

        if not success or frame is None:
            read_failures += 1
            print(f"WARNING: frame read failure #{read_failures}")

            if read_failures >= 30:
                print("ERROR: Too many consecutive frame failures.")
                break

            time.sleep(0.05)
            continue

        read_failures = 0

        frame_counter += 1
        fps_window_frames += 1

        now = time.time()

        if now - fps_window_start >= 1.0:
            measured_fps = fps_window_frames / (now - fps_window_start)
            fps_window_frames = 0
            fps_window_start = now

        height, width = frame.shape[:2]

        one_third = width // 3

        # LEFT / CENTER / RIGHT boundaries
        cv2.line(
            frame,
            (one_third, 0),
            (one_third, height),
            (255, 255, 255),
            2,
        )

        cv2.line(
            frame,
            (one_third * 2, 0),
            (one_third * 2, height),
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            "LEFT",
            (40, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            "CENTER",
            (one_third + 40, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            "RIGHT",
            (one_third * 2 + 40, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"FPS: {measured_fps:.1f}",
            (30, height - 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        elapsed = now - start_time

        cv2.putText(
            frame,
            f"Test: {elapsed:.0f}s / {TEST_DURATION_SECONDS}s",
            (30, height - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Atlas 6.0 - C950 Vision Baseline", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = OUTPUT_DIR / f"atlas_c950_{timestamp}.jpg"

            cv2.imwrite(str(filename), frame)

            saved_frames += 1

            print(f"Saved frame: {filename}")

        elif key == ord("q"):
            print("User ended test.")
            break

        if elapsed >= TEST_DURATION_SECONDS:
            print("10-minute baseline test completed.")
            break

    total_elapsed = time.time() - start_time

    cap.release()
    cv2.destroyAllWindows()

    average_fps = (
        frame_counter / total_elapsed
        if total_elapsed > 0
        else 0.0
    )

    print()
    print("=" * 60)
    print("TEST RESULT")
    print("=" * 60)
    print(f"Duration       : {total_elapsed:.1f} seconds")
    print(f"Frames         : {frame_counter}")
    print(f"Average FPS    : {average_fps:.2f}")
    print(f"Saved frames   : {saved_frames}")
    print(f"Final failures : {read_failures}")
    print("=" * 60)


if __name__ == "__main__":
    main()