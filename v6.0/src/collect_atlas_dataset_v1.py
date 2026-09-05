import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

import cv2


# ============================================================
# Atlas 6.0 - Stage 12A-2
# Dataset Collector V1
#
# Camera: EMEET C950
# Camera index: FIXED = 1
#
# PURPOSE
# - Capture real C950 frames.
# - Crop LEFT / CENTER / RIGHT navigation regions.
# - Save each crop directly into an Ultralytics
#   classification dataset:
#
#     Atlas_Vision_Dataset/
#       train/FREE
#       train/BLOCKED
#       train/EDGE
#       val/FREE
#       val/BLOCKED
#       val/EDGE
#       test/FREE
#       test/BLOCKED
#       test/EDGE
#
# - No S/Q keys.
# - Auto countdown, capture, save, and exit.
# - Unicode/Chinese Windows paths supported via
#   cv2.imencode(...).tofile(...).
#
# IMPORTANT
# - Labels are supplied by the user for each zone.
# - This program does NOT train a model.
# - This program does NOT control Atlas or ESP32.
# ============================================================


CAMERA_INDEX = 1
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30

VALID_LABELS = {"FREE", "BLOCKED", "EDGE"}
VALID_SPLITS = {"train", "val", "test"}

# Ignore the top part of the image, which is usually less
# relevant to tabletop navigation.
NAV_TOP_RATIO = 0.28

# Overlapping horizontal crops.
# LEFT   = 0%   -> 42%
# CENTER = 29%  -> 71%
# RIGHT  = 58%  -> 100%
ZONE_RANGES = {
    "LEFT": (0.00, 0.42),
    "CENTER": (0.29, 0.71),
    "RIGHT": (0.58, 1.00),
}


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


def save_jpeg_unicode_safe(path: Path, image, quality: int = 95) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)

    ok, encoded = cv2.imencode(
        ".jpg",
        image,
        [cv2.IMWRITE_JPEG_QUALITY, quality],
    )

    if not ok:
        return False

    try:
        encoded.tofile(str(path))
    except Exception as exc:
        print(f"WRITE EXCEPTION: {exc}")
        return False

    return path.exists() and path.stat().st_size > 0


def crop_zone(frame, zone_name: str):
    height, width = frame.shape[:2]

    nav_y1 = int(height * NAV_TOP_RATIO)
    x1_ratio, x2_ratio = ZONE_RANGES[zone_name]

    x1 = int(width * x1_ratio)
    x2 = int(width * x2_ratio)

    return frame[nav_y1:height, x1:x2].copy()


def make_preview(frame, labels):
    preview = frame.copy()
    height, width = preview.shape[:2]
    nav_y1 = int(height * NAV_TOP_RATIO)

    colors = {
        "FREE": (0, 220, 0),
        "BLOCKED": (0, 0, 255),
        "EDGE": (0, 200, 255),
    }

    for zone_name, (x1_ratio, x2_ratio) in ZONE_RANGES.items():
        x1 = int(width * x1_ratio)
        x2 = int(width * x2_ratio)
        label = labels[zone_name]
        color = colors[label]

        cv2.rectangle(
            preview,
            (x1, nav_y1),
            (x2 - 1, height - 1),
            color,
            3,
        )

        cv2.putText(
            preview,
            f"{zone_name}: {label}",
            (x1 + 12, nav_y1 + 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            color,
            2,
        )

    cv2.putText(
        preview,
        "DATA COLLECTION ONLY - NO MOTOR CONTROL",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    return preview


def get_class_counts(dataset_root: Path, split: str):
    counts = {}

    for label in sorted(VALID_LABELS):
        folder = dataset_root / split / label
        counts[label] = len(list(folder.glob("*.jpg"))) if folder.exists() else 0

    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Atlas 6.0 C950 classification dataset collector"
    )

    parser.add_argument(
        "--split",
        required=True,
        choices=sorted(VALID_SPLITS),
        help="Dataset split: train, val, or test",
    )

    parser.add_argument(
        "--left",
        required=True,
        choices=sorted(VALID_LABELS),
        help="Ground-truth label for LEFT zone",
    )

    parser.add_argument(
        "--center",
        required=True,
        choices=sorted(VALID_LABELS),
        help="Ground-truth label for CENTER zone",
    )

    parser.add_argument(
        "--right",
        required=True,
        choices=sorted(VALID_LABELS),
        help="Ground-truth label for RIGHT zone",
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="Number of frames to capture in this scenario (default: 5)",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=0.7,
        help="Seconds between saved samples (default: 0.7)",
    )

    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
        help="Seconds before capture begins (default: 3)",
    )

    args = parser.parse_args()

    if args.samples < 1 or args.samples > 30:
        print("ERROR: --samples must be between 1 and 30.")
        sys.exit(1)

    if args.interval < 0.2:
        print("ERROR: --interval must be at least 0.2 seconds.")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    dataset_root = script_dir / "Atlas_Vision_Dataset"
    evidence_root = script_dir / "collection_evidence"

    labels = {
        "LEFT": args.left,
        "CENTER": args.center,
        "RIGHT": args.right,
    }

    # Create complete Ultralytics classification structure now.
    for split in sorted(VALID_SPLITS):
        for label in sorted(VALID_LABELS):
            (dataset_root / split / label).mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_evidence_dir = evidence_root / f"{args.split}_{run_id}"
    run_evidence_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 76)
    print("Atlas 6.0 - Stage 12A-2 Dataset Collector V1")
    print("=" * 76)
    print(f"Camera index : {CAMERA_INDEX}")
    print(f"Split        : {args.split}")
    print(f"LEFT         : {labels['LEFT']}")
    print(f"CENTER       : {labels['CENTER']}")
    print(f"RIGHT        : {labels['RIGHT']}")
    print(f"Samples      : {args.samples}")
    print(f"Dataset root : {dataset_root}")
    print()

    print("LABEL CHECK:")
    print("  FREE    = this zone is physically traversable")
    print("  BLOCKED = object/wall blocks this zone")
    print("  EDGE    = tabletop boundary/drop is visible in this zone")
    print()
    print("If any label above is wrong for the real scene, press Ctrl+C NOW.")
    print()

    cap = open_camera(CAMERA_INDEX)

    if cap is None:
        print("ERROR: C950 could not be opened.")
        print("Close Windows Camera / Teams / Zoom / browser camera pages and retry.")
        sys.exit(2)

    saved_zone_images = 0
    failed_zone_images = 0

    try:
        # Warm-up.
        print("Camera warm-up...")
        for _ in range(30):
            cap.read()

        # Live preview during countdown.
        for remaining in range(args.countdown, 0, -1):
            start = time.time()

            while time.time() - start < 1.0:
                ok, frame = cap.read()

                if not ok or frame is None:
                    continue

                preview = make_preview(frame, labels)

                cv2.putText(
                    preview,
                    f"CAPTURE STARTS IN {remaining}",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2,
                )

                cv2.imshow("Atlas Dataset Collector", preview)
                cv2.waitKey(1)

            print(f"Capture starts in {remaining}...")

        print()
        print("CAPTURING. Keep the scene correctly labeled.")
        print("Small natural movement/lighting variation is useful;")
        print("do not completely change the scene during one run.")
        print()

        for sample_index in range(1, args.samples + 1):
            ok, frame = cap.read()

            if not ok or frame is None:
                print(f"[{sample_index}/{args.samples}] FRAME READ FAIL")
                time.sleep(args.interval)
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            # Save one full-frame evidence image per sample.
            evidence_path = (
                run_evidence_dir
                / f"FULL_{sample_index:02d}_{timestamp}.jpg"
            )

            evidence_ok = save_jpeg_unicode_safe(evidence_path, frame)

            if not evidence_ok:
                print(f"[{sample_index}/{args.samples}] WARNING: evidence save failed")

            # Save 3 labeled zone crops.
            sample_successes = 0

            for zone_name in ("LEFT", "CENTER", "RIGHT"):
                label = labels[zone_name]
                crop = crop_zone(frame, zone_name)

                filename = (
                    f"{run_id}_"
                    f"{sample_index:02d}_"
                    f"{zone_name}_"
                    f"{label}_"
                    f"{timestamp}.jpg"
                )

                output_path = dataset_root / args.split / label / filename

                if save_jpeg_unicode_safe(output_path, crop):
                    saved_zone_images += 1
                    sample_successes += 1
                else:
                    failed_zone_images += 1
                    print(f"SAVE FAIL: {output_path}")

            preview = make_preview(frame, labels)

            cv2.putText(
                preview,
                f"SAVED SAMPLE {sample_index}/{args.samples}",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Atlas Dataset Collector", preview)
            cv2.waitKey(1)

            print(
                f"[{sample_index}/{args.samples}] "
                f"zone crops saved: {sample_successes}/3"
            )

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print()
        print("Ctrl+C received. Collection stopped safely.")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    counts = get_class_counts(dataset_root, args.split)

    print()
    print("=" * 76)
    print("COLLECTION SUMMARY")
    print("=" * 76)
    print(f"Zone images saved : {saved_zone_images}")
    print(f"Zone save failures: {failed_zone_images}")
    print(f"Evidence folder   : {run_evidence_dir}")
    print(f"Dataset folder    : {dataset_root}")
    print()
    print(f"{args.split} FREE    : {counts['FREE']}")
    print(f"{args.split} BLOCKED : {counts['BLOCKED']}")
    print(f"{args.split} EDGE    : {counts['EDGE']}")
    print()

    if failed_zone_images == 0 and saved_zone_images > 0:
        print("DATA COLLECTION RUN: PASS")
    else:
        print("DATA COLLECTION RUN: CHECK REQUIRED")

    print("=" * 76)


if __name__ == "__main__":
    main()
