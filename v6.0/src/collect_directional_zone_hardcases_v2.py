"""
Atlas 6.0 - Directional Zone Hard-Case Collector V2
Collects ONLY one selected directional zone per run.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import cv2

CAMERA_INDEX_DEFAULT = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 30
IMGSZ = 224
PAD_COLOR = (114, 114, 114)


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
            print(f"CAMERA BACKEND: {name}")
            return cap
        cap.release()
    return None


def letterbox_square(image, size=IMGSZ):
    h, w = image.shape[:2]
    scale = min(size / w, size / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (nw, nh), interpolation=interpolation)
    left = (size - nw) // 2
    right = size - nw - left
    top = (size - nh) // 2
    bottom = size - nh - top
    return cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=PAD_COLOR
    )


def save_jpg(path: Path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError(f"Could not encode image: {path}")
    buf.tofile(str(path))


def crop_zone(frame, nav_top, x1r, x2r):
    h, w = frame.shape[:2]
    x1 = int(round(w * x1r))
    x2 = int(round(w * x2r))
    y1 = int(round(h * nav_top))
    return frame[y1:h, x1:x2].copy(), (x1, y1, x2, h)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--zone", required=True, choices=["LEFT", "CENTER", "RIGHT"])
    p.add_argument("--label", required=True, choices=["FREE", "BLOCKED"])
    p.add_argument("--samples", type=int, default=10)
    p.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    p.add_argument("--interval", type=float, default=0.45)
    p.add_argument("--countdown", type=int, default=3)
    args = p.parse_args()

    base = Path(__file__).resolve().parent
    release_json = base / "Atlas_Models" / "RELEASE_CANDIDATES" / "atlas_directional_release.json"
    if not release_json.exists():
        print("FAIL: directional release JSON not found:")
        print(release_json)
        raise SystemExit(1)

    cfg = load_json(release_json)
    nav_top = float(cfg["nav_top_ratio"])
    zones = cfg["zone_ranges"]
    x1r, x2r = zones[args.zone]

    print("=" * 82)
    print("Atlas 6.0 - Directional Zone Hard-Case Collector V2")
    print("=" * 82)
    print(f"Zone        : {args.zone}")
    print(f"Label       : {args.label}")
    print(f"Samples     : {args.samples}")
    print(f"NAV top     : {nav_top}")
    print(f"Zone range  : [{x1r}, {x2r}]")
    print("Source      : current atlas_directional_release.json")
    print()

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA CHECK: FAIL")
        raise SystemExit(2)

    for _ in range(30):
        cap.read()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_dir = base / "Directional_Hardcase_Raw" / run_id / args.zone / args.label
    prepared_dir = base / "Prepared_Atlas_Directional_Dataset" / "train" / args.label
    raw_dir.mkdir(parents=True, exist_ok=True)
    prepared_dir.mkdir(parents=True, exist_ok=True)

    print("IMPORTANT:")
    print("Keep the scene fixed during this run.")
    print(f"Only the {args.zone} zone will be saved.")
    print()

    try:
        for remaining in range(args.countdown, 0, -1):
            print(f"Starting in {remaining}...")
            deadline = time.time() + 1.0
            while time.time() < deadline:
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                _, box = crop_zone(frame, nav_top, x1r, x2r)
                x1, y1, x2, y2 = box
                display = frame.copy()
                cv2.rectangle(display, (x1, y1), (x2 - 1, y2 - 1), (255,255,255), 3)
                cv2.putText(
                    display, f"{args.zone} -> {args.label} | starts in {remaining}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2
                )
                cv2.imshow("Atlas Hard-Case Collector", display)
                cv2.waitKey(1)

        saved = 0
        next_save = time.time()

        while saved < args.samples:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            crop, box = crop_zone(frame, nav_top, x1r, x2r)
            x1, y1, x2, y2 = box
            display = frame.copy()
            cv2.rectangle(display, (x1, y1), (x2 - 1, y2 - 1), (255,255,255), 3)
            cv2.putText(
                display, f"{args.zone} -> {args.label} | {saved}/{args.samples}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2
            )
            cv2.imshow("Atlas Hard-Case Collector", display)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                print("User cancelled.")
                break

            now = time.time()
            if now < next_save:
                continue

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            raw_name = f"hardcase_{args.zone}_{args.label}_{stamp}_raw.jpg"
            prepared_name = f"hardcase_{args.zone}_{args.label}_{stamp}.jpg"

            save_jpg(raw_dir / raw_name, crop)
            save_jpg(prepared_dir / prepared_name, letterbox_square(crop))

            saved += 1
            next_save = now + args.interval
            print(f"SAVED {saved:02d}/{args.samples} | {args.zone} | {args.label}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print()
    print("=" * 82)
    print("COLLECTION COMPLETE")
    print("=" * 82)
    print(f"Raw evidence : {raw_dir}")
    print(f"Training data: {prepared_dir}")
    print("No validation images were modified.")


if __name__ == "__main__":
    main()
