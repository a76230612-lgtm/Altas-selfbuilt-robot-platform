import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

import cv2


# ============================================================
# Atlas 6.0 - Stage 12A-2
# Dataset Collector V2
#
# Camera: EMEET C950
# Camera index: FIXED = 1
#
# TWO DATASETS:
#
# 1) Directional Traversability Dataset
#    - LEFT / CENTER / RIGHT crops
#    - Classes: FREE / BLOCKED
#
# 2) Global Edge Dataset
#    - Full camera frame
#    - Classes: SAFE / EDGE
#
# FINAL RUNTIME LOGIC:
#    if GlobalEdgeModel == EDGE:
#        LEFT = EDGE
#        CENTER = EDGE
#        RIGHT = EDGE
#    else:
#        classify LEFT/CENTER/RIGHT as FREE/BLOCKED
#
# No S/Q required.
# Unicode/Chinese Windows paths supported.
# ============================================================


CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30

VALID_SPLITS = {"train", "val", "test"}
DIRECTIONAL_LABELS = {"FREE", "BLOCKED"}
EDGE_LABELS = {"SAFE", "EDGE"}

NAV_TOP_RATIO = 0.28

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


def preview_directional(frame, labels):
    preview = frame.copy()
    height, width = preview.shape[:2]
    nav_y1 = int(height * NAV_TOP_RATIO)

    colors = {
        "FREE": (0, 220, 0),
        "BLOCKED": (0, 0, 255),
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
        "DIRECTIONAL DATA: FREE / BLOCKED",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    return preview


def preview_edge(frame, scene_label):
    preview = frame.copy()

    color = (0, 0, 255) if scene_label == "EDGE" else (0, 220, 0)

    cv2.rectangle(
        preview,
        (3, 3),
        (preview.shape[1] - 4, preview.shape[0] - 4),
        color,
        6,
    )

    cv2.putText(
        preview,
        f"GLOBAL SCENE: {scene_label}",
        (20, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        color,
        3,
    )

    if scene_label == "EDGE":
        cv2.putText(
            preview,
            "RUNTIME OVERRIDE: LEFT=EDGE CENTER=EDGE RIGHT=EDGE",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
        )

    return preview


def create_dataset_structure(script_dir: Path):
    directional_root = script_dir / "Atlas_Directional_Dataset"
    edge_root = script_dir / "Atlas_Edge_Dataset"

    for split in sorted(VALID_SPLITS):
        for label in sorted(DIRECTIONAL_LABELS):
            (directional_root / split / label).mkdir(parents=True, exist_ok=True)

        for label in sorted(EDGE_LABELS):
            (edge_root / split / label).mkdir(parents=True, exist_ok=True)

    return directional_root, edge_root


def count_images(root: Path, split: str, labels):
    result = {}

    for label in sorted(labels):
        folder = root / split / label
        result[label] = len(list(folder.glob("*.jpg")))

    return result


def run_countdown(cap, seconds, preview_builder):
    for remaining in range(seconds, 0, -1):
        start = time.time()

        while time.time() - start < 1.0:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            preview = preview_builder(frame)

            cv2.putText(
                preview,
                f"CAPTURE STARTS IN {remaining}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Atlas Dataset Collector V2", preview)
            cv2.waitKey(1)

        print(f"Capture starts in {remaining}...")


def main():
    parser = argparse.ArgumentParser(
        description="Atlas 6.0 Dataset Collector V2"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["directional", "edge"],
        help="directional = FREE/BLOCKED zone crops; edge = SAFE/EDGE full frames",
    )

    parser.add_argument(
        "--split",
        required=True,
        choices=sorted(VALID_SPLITS),
    )

    parser.add_argument("--left", choices=sorted(DIRECTIONAL_LABELS))
    parser.add_argument("--center", choices=sorted(DIRECTIONAL_LABELS))
    parser.add_argument("--right", choices=sorted(DIRECTIONAL_LABELS))

    parser.add_argument(
        "--scene",
        choices=sorted(EDGE_LABELS),
        help="SAFE or EDGE; required in --mode edge",
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=0.7,
    )

    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    if args.samples < 1 or args.samples > 30:
        print("ERROR: --samples must be between 1 and 30.")
        sys.exit(1)

    if args.interval < 0.2:
        print("ERROR: --interval must be >= 0.2 seconds.")
        sys.exit(1)

    if args.mode == "directional":
        if not args.left or not args.center or not args.right:
            print(
                "ERROR: directional mode requires "
                "--left, --center, and --right."
            )
            sys.exit(1)

    if args.mode == "edge":
        if not args.scene:
            print("ERROR: edge mode requires --scene SAFE or --scene EDGE.")
            sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    directional_root, edge_root = create_dataset_structure(script_dir)

    evidence_root = script_dir / "collection_evidence_v2"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = evidence_root / f"{args.mode}_{args.split}_{run_id}"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 78)
    print("Atlas 6.0 - Stage 12A-2 Dataset Collector V2")
    print("=" * 78)
    print(f"Camera index : {CAMERA_INDEX}")
    print(f"Mode         : {args.mode}")
    print(f"Split        : {args.split}")
    print(f"Samples      : {args.samples}")

    if args.mode == "directional":
        labels = {
            "LEFT": args.left,
            "CENTER": args.center,
            "RIGHT": args.right,
        }

        print(f"LEFT         : {args.left}")
        print(f"CENTER       : {args.center}")
        print(f"RIGHT        : {args.right}")
        print(f"Dataset root : {directional_root}")
        print()
        print("EDGE is NOT labeled here.")
        print("Directional model only learns FREE vs BLOCKED.")

        preview_builder = lambda frame: preview_directional(frame, labels)

    else:
        print(f"Scene label  : {args.scene}")
        print(f"Dataset root : {edge_root}")
        print()
        print("EDGE is a GLOBAL scene state.")
        print("At runtime, EDGE overrides all three directions.")

        preview_builder = lambda frame: preview_edge(frame, args.scene)

    print()
    print("If the real scene does not match these labels, press Ctrl+C now.")
    print()

    cap = open_camera(CAMERA_INDEX)

    if cap is None:
        print("ERROR: C950 could not be opened.")
        print("Close Camera / Teams / Zoom / browser camera pages and retry.")
        sys.exit(2)

    saved = 0
    failed = 0

    try:
        print("Camera warm-up...")
        for _ in range(30):
            cap.read()

        run_countdown(cap, args.countdown, preview_builder)

        print()
        print("CAPTURING...")
        print()

        for sample_index in range(1, args.samples + 1):
            ok, frame = cap.read()

            if not ok or frame is None:
                print(f"[{sample_index}/{args.samples}] FRAME READ FAIL")
                time.sleep(args.interval)
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            evidence_path = (
                evidence_dir
                / f"FULL_{sample_index:02d}_{timestamp}.jpg"
            )
            save_jpeg_unicode_safe(evidence_path, frame)

            if args.mode == "directional":
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

                    output_path = (
                        directional_root
                        / args.split
                        / label
                        / filename
                    )

                    if save_jpeg_unicode_safe(output_path, crop):
                        saved += 1
                        sample_successes += 1
                    else:
                        failed += 1

                print(
                    f"[{sample_index}/{args.samples}] "
                    f"direction crops saved: {sample_successes}/3"
                )

            else:
                filename = (
                    f"{run_id}_"
                    f"{sample_index:02d}_"
                    f"{args.scene}_"
                    f"{timestamp}.jpg"
                )

                output_path = (
                    edge_root
                    / args.split
                    / args.scene
                    / filename
                )

                if save_jpeg_unicode_safe(output_path, frame):
                    saved += 1
                    print(
                        f"[{sample_index}/{args.samples}] "
                        f"global {args.scene} frame saved"
                    )
                else:
                    failed += 1
                    print(
                        f"[{sample_index}/{args.samples}] SAVE FAIL"
                    )

            preview = preview_builder(frame)

            cv2.putText(
                preview,
                f"SAVED SAMPLE {sample_index}/{args.samples}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Atlas Dataset Collector V2", preview)
            cv2.waitKey(1)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print()
        print("Ctrl+C received. Collection stopped safely.")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print()
    print("=" * 78)
    print("COLLECTION SUMMARY")
    print("=" * 78)
    print(f"Saved             : {saved}")
    print(f"Failed            : {failed}")
    print(f"Evidence folder   : {evidence_dir}")

    if args.mode == "directional":
        counts = count_images(
            directional_root,
            args.split,
            DIRECTIONAL_LABELS,
        )

        print(f"{args.split} FREE       : {counts['FREE']}")
        print(f"{args.split} BLOCKED    : {counts['BLOCKED']}")

    else:
        counts = count_images(
            edge_root,
            args.split,
            EDGE_LABELS,
        )

        print(f"{args.split} SAFE       : {counts['SAFE']}")
        print(f"{args.split} EDGE       : {counts['EDGE']}")

    if failed == 0 and saved > 0:
        print("DATA COLLECTION RUN: PASS")
    else:
        print("DATA COLLECTION RUN: CHECK REQUIRED")

    print("=" * 78)


if __name__ == "__main__":
    main()
