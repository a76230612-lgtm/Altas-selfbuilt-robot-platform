import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np

# ============================================================
# Atlas 6.0 - Near-Field EDGE ROI Collector V1
#
# Camera: EMEET C950, index 1
#
# NEW EDGE DEFINITION:
# - Only the LOWER 50% of the camera frame is used for EDGE safety.
# - SAFE = continuous tabletop in the near-field ROI.
# - EDGE = tabletop termination/drop is visible in the near-field ROI.
#
# The saved training image is already 224x224 letterboxed, so
# Ultralytics classification will not crop away left/right content.
#
# Full-frame evidence images with the ROI rectangle are also saved.
# No keyboard input required.
# ============================================================

CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30

ROI_TOP_RATIO = 0.50
TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)

VALID_SPLITS = {"train", "val", "test"}
VALID_LABELS = {"SAFE", "EDGE"}


def open_camera(index):
    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF),
        ("ANY", cv2.CAP_ANY),
    ]

    for name, backend in backends:
        print(f"Trying backend: {name}")
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
            print(f"Camera opened: {name}")
            return cap

        cap.release()

    return None


def save_jpeg(path, image, quality=95):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, enc = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return False
    enc.tofile(str(path))
    return path.exists() and path.stat().st_size > 0


def near_field_roi(frame):
    h, w = frame.shape[:2]
    y1 = int(h * ROI_TOP_RATIO)
    return frame[y1:h, 0:w].copy(), y1


def letterbox_square(image, size=TARGET_SIZE):
    h, w = image.shape[:2]
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


def make_preview(frame, label):
    preview = frame.copy()
    h, w = preview.shape[:2]
    y1 = int(h * ROI_TOP_RATIO)

    color = (0, 220, 0) if label == "SAFE" else (0, 0, 255)

    cv2.rectangle(preview, (0, y1), (w - 1, h - 1), color, 4)
    cv2.putText(
        preview,
        f"NEAR-FIELD ROI: {label}",
        (20, y1 + 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2,
    )
    cv2.putText(
        preview,
        "ONLY THIS LOWER AREA DECIDES EDGE",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    return preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=sorted(VALID_SPLITS))
    parser.add_argument("--label", required=True, choices=sorted(VALID_LABELS))
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--interval", type=float, default=0.7)
    parser.add_argument("--countdown", type=int, default=3)
    args = parser.parse_args()

    if not (1 <= args.samples <= 30):
        print("ERROR: --samples must be 1..30")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent
    dataset_root = base_dir / "Atlas_Edge_ROI_Dataset"
    evidence_root = base_dir / "Atlas_Edge_ROI_Evidence"

    for split in sorted(VALID_SPLITS):
        for label in sorted(VALID_LABELS):
            (dataset_root / split / label).mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_evidence = evidence_root / f"{args.split}_{args.label}_{run_id}"
    run_evidence.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("Atlas 6.0 - Near-Field EDGE ROI Collector V1")
    print("=" * 78)
    print(f"Split      : {args.split}")
    print(f"Label      : {args.label}")
    print(f"Samples    : {args.samples}")
    print(f"ROI        : lower {int((1 - ROI_TOP_RATIO) * 100)}% of full frame")
    print(f"Dataset    : {dataset_root}")
    print()
    print("LABEL RULE:")
    print("SAFE = near-field ROI still contains continuous tabletop.")
    print("EDGE = tabletop termination/drop enters the near-field ROI.")
    print()
    print("If the real scene does not match the label, press Ctrl+C now.")
    print()

    cap = open_camera(CAMERA_INDEX)
    if cap is None:
        print("ERROR: C950 could not be opened.")
        sys.exit(2)

    try:
        print("Camera warm-up...")
        for _ in range(30):
            cap.read()

        for remaining in range(args.countdown, 0, -1):
            start = time.time()
            while time.time() - start < 1.0:
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                preview = make_preview(frame, args.label)
                cv2.putText(
                    preview,
                    f"CAPTURE STARTS IN {remaining}",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2,
                )
                cv2.imshow("Atlas EDGE ROI Collector", preview)
                cv2.waitKey(1)
            print(f"Capture starts in {remaining}...")

        saved = 0
        failed = 0

        for i in range(1, args.samples + 1):
            ok, frame = cap.read()
            if not ok or frame is None:
                print(f"[{i}/{args.samples}] FRAME READ FAIL")
                failed += 1
                continue

            roi, _ = near_field_roi(frame)
            prepared = letterbox_square(roi)

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            out = (
                dataset_root
                / args.split
                / args.label
                / f"{run_id}_{i:02d}_{args.label}_{stamp}.jpg"
            )

            preview = make_preview(frame, args.label)
            evidence = (
                run_evidence
                / f"FULL_{i:02d}_{stamp}.jpg"
            )

            ok1 = save_jpeg(out, prepared)
            ok2 = save_jpeg(evidence, preview)

            if ok1 and ok2:
                saved += 1
                print(f"[{i}/{args.samples}] SAVED")
            else:
                failed += 1
                print(f"[{i}/{args.samples}] SAVE FAIL")

            cv2.imshow("Atlas EDGE ROI Collector", preview)
            cv2.waitKey(1)
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("Stopped safely by Ctrl+C.")
        cap.release()
        cv2.destroyAllWindows()
        sys.exit(3)

    cap.release()
    cv2.destroyAllWindows()

    print()
    print("=" * 78)
    print(f"Saved  : {saved}")
    print(f"Failed : {failed}")
    print(f"Dataset: {dataset_root}")
    print(f"Evidence: {run_evidence}")
    print(
        "COLLECTION RESULT: PASS"
        if failed == 0 and saved > 0
        else "COLLECTION RESULT: CHECK REQUIRED"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
