import cv2
import numpy as np
import time
import csv
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================
# Atlas 6.0
# Stage 12A-1 Vision Free-Space Baseline V1
#
# PURPOSE
# ------------------------------------------------------------
# 1. Read live video from EMEET C950.
# 2. Use the nearest visible tabletop region as an adaptive
#    appearance reference.
# 3. Estimate connected tabletop/free-space in:
#       LEFT / CENTER / RIGHT
# 4. Automatically save RAW and ANNOTATED frames.
# 5. Automatically write vision scores to CSV.
#
# IMPORTANT
# ------------------------------------------------------------
# - This version DOES NOT control Atlas.
# - This version DOES NOT control ESP32.
# - This is NOT a cliff-safety system.
# - This is NOT final obstacle avoidance.
# - It is a perception baseline only.
# ============================================================


# ---------------- GENERAL SETTINGS ----------------

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30

# Program automatically ends after this many seconds.
TEST_DURATION_SECONDS = 120

# Automatically save one sample every N seconds.
AUTO_SAVE_INTERVAL_SECONDS = 2.0

# Print scores to terminal every N seconds.
PRINT_INTERVAL_SECONDS = 0.5


# ---------------- NAVIGATION REGION ----------------

# Ignore much of the upper image.
# Navigation analysis begins here.
NAV_TOP_RATIO = 0.38

# Do not use the extreme bottom edge of the image.
NAV_BOTTOM_RATIO = 0.96


# ---------------- TABLE REFERENCE PATCH ----------------
#
# This small rectangle should normally contain tabletop
# immediately in front of Atlas.
#
# X range is centered.
# Y range is near the bottom.

SEED_X_MIN_RATIO = 0.42
SEED_X_MAX_RATIO = 0.58

SEED_Y_MIN_RATIO = 0.78
SEED_Y_MAX_RATIO = 0.91


# ---------------- VISUAL CLASSIFICATION ----------------
#
# These values are ONLY initial software-baseline thresholds.
# They are NOT physical safety thresholds.

FREE_SCORE_THRESHOLD = 0.58
BLOCKED_SCORE_THRESHOLD = 0.35

MIN_COLOR_TOLERANCE = 16.0
MAX_COLOR_TOLERANCE = 48.0


# ============================================================
# CAMERA
# ============================================================

def open_camera(index): 1
    """
    Try several Windows camera backends.
    This increases success rate across different Windows PCs.
    """

    backends = [
        cv2.CAP_DSHOW,
        cv2.CAP_MSMF,
        cv2.CAP_ANY,
    ]

    for backend in backends:

        cap = cv2.VideoCapture(index, backend)

        if not cap.isOpened():
            cap.release()
            continue

        # Ask camera for MJPG.
        # This often improves USB webcam FPS at 720p.
        cap.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG"),
        )

        cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH,
        )

        cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT,
        )

        cap.set(
            cv2.CAP_PROP_FPS,
            TARGET_FPS,
        )

        # Test actual frame.
        success, frame = cap.read()

        if success and frame is not None:
            return cap

        cap.release()

    return None


# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def classify_score(score):

    if score >= FREE_SCORE_THRESHOLD:
        return "FREE"

    if score <= BLOCKED_SCORE_THRESHOLD:
        return "BLOCKED"

    return "UNCERTAIN"


def get_zone_color(status):

    if status == "FREE":
        return (0, 220, 0)

    if status == "BLOCKED":
        return (0, 0, 255)

    return (0, 200, 255)


# ============================================================
# FLOOR / TABLETOP SEGMENTATION
# ============================================================

def calculate_table_mask(frame):
    """
    Learn tabletop appearance from a seed patch near the
    lower-center of the current frame.

    Then determine which pixels in the lower navigation area
    look visually similar.

    Finally retain the connected region that overlaps the
    known tabletop seed.
    """

    height, width = frame.shape[:2]

    nav_y1 = int(height * NAV_TOP_RATIO)
    nav_y2 = int(height * NAV_BOTTOM_RATIO)

    seed_x1 = int(width * SEED_X_MIN_RATIO)
    seed_x2 = int(width * SEED_X_MAX_RATIO)

    seed_y1 = int(height * SEED_Y_MIN_RATIO)
    seed_y2 = int(height * SEED_Y_MAX_RATIO)

    lab = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2LAB,
    ).astype(np.float32)

    seed = lab[
        seed_y1:seed_y2,
        seed_x1:seed_x2
    ]

    if seed.size == 0:
        return None

    seed_pixels = seed.reshape(-1, 3)

    median_color = np.median(
        seed_pixels,
        axis=0,
    )

    seed_distances = np.linalg.norm(
        seed_pixels - median_color,
        axis=1,
    )

    # Adaptive tolerance based on actual tabletop variation.
    percentile_95 = float(
        np.percentile(seed_distances, 95)
    )

    tolerance = percentile_95 * 2.4

    tolerance = clamp(
        tolerance,
        MIN_COLOR_TOLERANCE,
        MAX_COLOR_TOLERANCE,
    )

    nav_lab = lab[
        nav_y1:nav_y2,
        :
    ]

    distance = np.linalg.norm(
        nav_lab - median_color,
        axis=2,
    )

    floor_like = (
        distance <= tolerance
    ).astype(np.uint8) * 255

    # Reduce isolated noise.
    kernel_small = np.ones(
        (5, 5),
        np.uint8,
    )

    kernel_large = np.ones(
        (9, 9),
        np.uint8,
    )

    floor_like = cv2.morphologyEx(
        floor_like,
        cv2.MORPH_OPEN,
        kernel_small,
    )

    floor_like = cv2.morphologyEx(
        floor_like,
        cv2.MORPH_CLOSE,
        kernel_large,
    )

    # --------------------------------------------------------
    # Connected component selection
    #
    # We do not simply accept every tabletop-colored pixel.
    # We keep the region connected to the known near-table
    # patch.
    # --------------------------------------------------------

    number_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            floor_like,
            connectivity=8,
        )
    )

    seed_nav_y1 = max(
        0,
        seed_y1 - nav_y1,
    )

    seed_nav_y2 = min(
        floor_like.shape[0],
        seed_y2 - nav_y1,
    )

    best_label = 0
    best_overlap = 0

    for label in range(1, number_labels):

        component_seed = (
            labels[
                seed_nav_y1:seed_nav_y2,
                seed_x1:seed_x2
            ]
            == label
        )

        overlap = int(
            np.count_nonzero(component_seed)
        )

        if overlap > best_overlap:
            best_overlap = overlap
            best_label = label

    connected_floor = np.zeros_like(
        floor_like,
        dtype=np.uint8,
    )

    if best_label > 0:

        connected_floor[
            labels == best_label
        ] = 255

    return {
        "mask": connected_floor,
        "nav_y1": nav_y1,
        "nav_y2": nav_y2,
        "seed_box": (
            seed_x1,
            seed_y1,
            seed_x2,
            seed_y2,
        ),
        "tolerance": tolerance,
    }


# ============================================================
# LEFT / CENTER / RIGHT SCORE
# ============================================================

def calculate_zone_scores(mask):
    """
    Divide navigation mask into three vertical zones.
    Calculate connected-floor percentage in each zone.
    """

    height, width = mask.shape

    one_third = width // 3

    zones = {
        "LEFT": (
            0,
            one_third,
        ),
        "CENTER": (
            one_third,
            one_third * 2,
        ),
        "RIGHT": (
            one_third * 2,
            width,
        ),
    }

    results = {}

    # Focus more strongly on the lower 72% of navigation ROI.
    analysis_y1 = int(
        height * 0.28
    )

    analysis = mask[
        analysis_y1:height,
        :
    ]

    for name, (x1, x2) in zones.items():

        zone = analysis[
            :,
            x1:x2
        ]

        total = zone.size

        free_pixels = int(
            np.count_nonzero(zone)
        )

        if total > 0:
            score = free_pixels / total
        else:
            score = 0.0

        results[name] = {
            "score": score,
            "status": classify_score(score),
        }

    return results


# ============================================================
# DISPLAY
# ============================================================

def create_annotated_frame(
    frame,
    table_data,
    zone_results,
    measured_fps,
):
    output = frame.copy()

    height, width = frame.shape[:2]

    nav_y1 = table_data["nav_y1"]
    nav_y2 = table_data["nav_y2"]

    seed_x1, seed_y1, seed_x2, seed_y2 = (
        table_data["seed_box"]
    )

    mask = table_data["mask"]

    # --------------------------------------------------------
    # Overlay detected connected tabletop
    # --------------------------------------------------------

    overlay = output.copy()

    nav_area = overlay[
        nav_y1:nav_y2,
        :
    ]

    green_layer = np.zeros_like(nav_area)

    green_layer[:, :, 1] = mask

    blended = cv2.addWeighted(
        nav_area,
        0.72,
        green_layer,
        0.28,
        0,
    )

    overlay[
        nav_y1:nav_y2,
        :
    ] = blended

    output = overlay

    # --------------------------------------------------------
    # Navigation ROI
    # --------------------------------------------------------

    cv2.rectangle(
        output,
        (0, nav_y1),
        (width - 1, nav_y2),
        (255, 255, 255),
        2,
    )

    # --------------------------------------------------------
    # Seed region
    # --------------------------------------------------------

    cv2.rectangle(
        output,
        (seed_x1, seed_y1),
        (seed_x2, seed_y2),
        (255, 0, 255),
        2,
    )

    cv2.putText(
        output,
        "TABLE REFERENCE",
        (
            seed_x1,
            max(30, seed_y1 - 10),
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 0, 255),
        2,
    )

    # --------------------------------------------------------
    # LEFT/CENTER/RIGHT boundaries
    # --------------------------------------------------------

    third = width // 3

    cv2.line(
        output,
        (third, nav_y1),
        (third, nav_y2),
        (255, 255, 255),
        2,
    )

    cv2.line(
        output,
        (third * 2, nav_y1),
        (third * 2, nav_y2),
        (255, 255, 255),
        2,
    )

    zone_centers = {
        "LEFT": third // 2,
        "CENTER": third + third // 2,
        "RIGHT": third * 2 + third // 2,
    }

    for name in [
        "LEFT",
        "CENTER",
        "RIGHT",
    ]:

        result = zone_results[name]

        score = result["score"]
        status = result["status"]

        color = get_zone_color(status)

        text_1 = (
            f"{name}: {score:.2f}"
        )

        text_2 = status

        x = zone_centers[name] - 100

        cv2.putText(
            output,
            text_1,
            (x, nav_y1 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            color,
            2,
        )

        cv2.putText(
            output,
            text_2,
            (x, nav_y1 + 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            color,
            2,
        )

    # --------------------------------------------------------
    # FPS / threshold
    # --------------------------------------------------------

    cv2.putText(
        output,
        f"FPS: {measured_fps:.1f}",
        (25, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        output,
        (
            "Adaptive table tolerance: "
            f"{table_data['tolerance']:.1f}"
        ),
        (25, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        output,
        "PERCEPTION ONLY - NO MOTOR CONTROL",
        (25, height - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 0, 255),
        2,
    )

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Windows camera index",
    )

    args = parser.parse_args()

    camera_index = args.camera

    print()
    print("=" * 70)
    print("Atlas 6.0 - Stage 12A-1")
    print("Vision Free-Space Baseline V1")
    print("=" * 70)

    script_dir = Path(
        __file__
    ).resolve().parent

    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    result_root = (
        script_dir
        / "results"
        / run_id
    )

    raw_dir = (
        result_root
        / "raw"
    )

    annotated_dir = (
        result_root
        / "annotated"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    annotated_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        result_root
        / "vision_log.csv"
    )

    print()
    print(
        f"Opening camera index {camera_index}..."
    )

    cap = open_camera(
        camera_index
    )

    if cap is None:

        print()
        print(
            "ERROR: Camera could not be opened."
        )

        print(
            "Use the SAME camera index that worked "
            "in the previous C950 test."
        )

        return

    actual_width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    actual_height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    reported_fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    print()
    print("Camera opened successfully.")
    print(
        f"Resolution: "
        f"{actual_width} x {actual_height}"
    )

    print(
        f"Camera reported FPS: "
        f"{reported_fps:.2f}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "The program will save images AUTOMATICALLY."
    )

    print(
        "No S key is required."
    )

    print(
        "No Q key is required."
    )

    print(
        "To stop early, use Ctrl+C in PowerShell."
    )

    print()

    csv_file = open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    )

    writer = csv.writer(
        csv_file
    )

    writer.writerow([
        "timestamp",
        "elapsed_seconds",
        "left_score",
        "left_status",
        "center_score",
        "center_status",
        "right_score",
        "right_status",
        "adaptive_tolerance",
        "measured_fps",
    ])

    start_time = time.time()

    next_save_time = (
        start_time + 2.0
    )

    next_print_time = start_time

    fps_start = start_time
    fps_frames = 0
    measured_fps = 0.0

    total_frames = 0
    saved_samples = 0
    read_failures = 0

    try:

        while True:

            success, frame = cap.read()

            now = time.time()

            elapsed = (
                now - start_time
            )

            if (
                not success
                or frame is None
            ):

                read_failures += 1

                print(
                    "WARNING: "
                    f"camera frame failure "
                    f"#{read_failures}"
                )

                if read_failures >= 30:

                    print(
                        "ERROR: "
                        "Too many camera failures."
                    )

                    break

                time.sleep(0.03)

                continue

            read_failures = 0

            total_frames += 1
            fps_frames += 1

            if (
                now - fps_start
                >= 1.0
            ):

                measured_fps = (
                    fps_frames
                    / (
                        now
                        - fps_start
                    )
                )

                fps_frames = 0
                fps_start = now

            table_data = (
                calculate_table_mask(
                    frame
                )
            )

            if table_data is None:

                print(
                    "WARNING: "
                    "Could not calculate "
                    "table mask."
                )

                continue

            zone_results = (
                calculate_zone_scores(
                    table_data["mask"]
                )
            )

            annotated = (
                create_annotated_frame(
                    frame,
                    table_data,
                    zone_results,
                    measured_fps,
                )
            )

            # ------------------------------------------------
            # Terminal output
            # ------------------------------------------------

            if now >= next_print_time:

                left = (
                    zone_results["LEFT"]
                )

                center = (
                    zone_results["CENTER"]
                )

                right = (
                    zone_results["RIGHT"]
                )

                print(
                    f"{elapsed:6.1f}s | "
                    f"L {left['score']:.2f} "
                    f"{left['status']:9s} | "
                    f"C {center['score']:.2f} "
                    f"{center['status']:9s} | "
                    f"R {right['score']:.2f} "
                    f"{right['status']:9s}"
                )

                next_print_time = (
                    now
                    + PRINT_INTERVAL_SECONDS
                )

            # ------------------------------------------------
            # CSV log
            # ------------------------------------------------

            writer.writerow([
                datetime.now().isoformat(
                    timespec="milliseconds"
                ),
                f"{elapsed:.3f}",
                f"{zone_results['LEFT']['score']:.4f}",
                zone_results["LEFT"]["status"],
                f"{zone_results['CENTER']['score']:.4f}",
                zone_results["CENTER"]["status"],
                f"{zone_results['RIGHT']['score']:.4f}",
                zone_results["RIGHT"]["status"],
                f"{table_data['tolerance']:.3f}",
                f"{measured_fps:.3f}",
            ])

            csv_file.flush()

            # ------------------------------------------------
            # Automatic image saving
            # ------------------------------------------------

            if now >= next_save_time:

                timestamp = (
                    datetime.now()
                    .strftime(
                        "%Y%m%d_%H%M%S_%f"
                    )
                )

                raw_path = (
                    raw_dir
                    / f"raw_{timestamp}.jpg"
                )

                annotated_path = (
                    annotated_dir
                    / f"vision_{timestamp}.jpg"
                )

                cv2.imwrite(
                    str(raw_path),
                    frame,
                )

                cv2.imwrite(
                    str(annotated_path),
                    annotated,
                )

                saved_samples += 1

                print(
                    f"  AUTO SAVED sample "
                    f"#{saved_samples}"
                )

                next_save_time = (
                    now
                    + AUTO_SAVE_INTERVAL_SECONDS
                )

            # ------------------------------------------------
            # Display
            # ------------------------------------------------

            cv2.imshow(
                "Atlas 6.0 - "
                "Stage 12A-1 Vision",
                annotated,
            )

            # We still process window events,
            # but no keyboard command is required.
            cv2.waitKey(1)

            if (
                elapsed
                >= TEST_DURATION_SECONDS
            ):

                print()
                print(
                    "Automatic test duration completed."
                )

                break

    except KeyboardInterrupt:

        print()
        print(
            "Ctrl+C received. "
            "Ending test safely."
        )

    finally:

        cap.release()

        cv2.destroyAllWindows()

        csv_file.close()

    total_elapsed = (
        time.time()
        - start_time
    )

    average_fps = (
        total_frames
        / total_elapsed
        if total_elapsed > 0
        else 0.0
    )

    print()
    print("=" * 70)
    print("STAGE 12A-1 SOFTWARE TEST SUMMARY")
    print("=" * 70)

    print(
        f"Duration       : "
        f"{total_elapsed:.1f} s"
    )

    print(
        f"Frames         : "
        f"{total_frames}"
    )

    print(
        f"Average FPS    : "
        f"{average_fps:.2f}"
    )

    print(
        f"Saved samples  : "
        f"{saved_samples}"
    )

    print(
        f"Result folder  : "
        f"{result_root}"
    )

    print()
    print(
        "This is perception-only evidence."
    )

    print(
        "Do NOT mark autonomous navigation "
        "or cliff safety as passed."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()