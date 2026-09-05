"""
Atlas 6.0 - CENTER-Only Dataset Collector V1
--------------------------------------------
Purpose:
  Build an independent CENTER FREE/BLOCKED dataset without changing
  the already-passing LEFT/RIGHT Directional V2 model.

Geometry:
  Reads nav_top_ratio and CENTER zone_range directly from the frozen
  atlas_directional_release.json so training and live runtime geometry match.

Output:
  Atlas_Center_Dataset/{train,val,test}/{FREE,BLOCKED}
  Center_Dataset_Evidence/...

Images are saved directly as 224x224 letterboxed crops.
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


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def open_camera(index):
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


def save_jpg(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError(f"JPEG encode failed: {path}")
    buf.tofile(str(path))


def crop_center(frame, nav_top, center_range):
    h, w = frame.shape[:2]
    x1 = int(round(w * float(center_range[0])))
    x2 = int(round(w * float(center_range[1])))
    y1 = int(round(h * float(nav_top)))
    return frame[y1:h, x1:x2].copy(), (x1, y1, x2, h)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", required=True, choices=["train", "val", "test"])
    p.add_argument("--label", required=True, choices=["FREE", "BLOCKED"])
    p.add_argument("--samples", type=int, default=5)
    p.add_argument("--camera", type=int, default=CAMERA_INDEX_DEFAULT)
    p.add_argument("--interval", type=float, default=0.45)
    p.add_argument("--countdown", type=int, default=3)
    args = p.parse_args()

    base = Path(__file__).resolve().parent
    release_json = (
        base / "Atlas_Models" / "RELEASE_CANDIDATES" /
        "atlas_directional_release.json"
    )

    if not release_json.exists():
        print("FAIL: missing directional release JSON:")
        print(release_json)
        raise SystemExit(1)

    cfg = load_json(release_json)
    nav_top = float(cfg["nav_top_ratio"])
    center_range = cfg["zone_ranges"]["CENTER"]

    dataset_dir = (
        base / "Atlas_Center_Dataset" /
        args.split / args.label
    )
    evidence_dir = (
        base / "Center_Dataset_Evidence" /
        args.split / args.label
    )

    print("=" * 86)
    print("Atlas 6.0 - CENTER-Only Dataset Collector V1")
    print("=" * 86)
    print(f"Split        : {args.split}")
    print(f"Label        : {args.label}")
    print(f"Samples      : {args.samples}")
    print(f"NAV top      : {nav_top}")
    print(f"CENTER range : {center_range}")
    print("Geometry src : atlas_directional_release.json")
    print()

    cap = open_camera(args.camera)
    if cap is None:
        print("CAMERA CHECK: FAIL")
        raise SystemExit(2)

    for _ in range(30):
        cap.read()

    try:
        for remaining in range(args.countdown, 0, -1):
            print(f"Starting in {remaining}...")
            deadline = time.time() + 1.0

            while time.time() < deadline:
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue

                _, box = crop_center(frame, nav_top, center_range)
                x1, y1, x2, y2 = box
                display = frame.copy()

                cv2.rectangle(
                    display, (x1, y1), (x2 - 1, y2 - 1),
                    (255, 255, 255), 3
                )

                cv2.putText(
                    display,
                    f"CENTER -> {args.label} | {args.split} | starts {remaining}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2
                )

                cv2.imshow("Atlas CENTER Collector", display)
                cv2.waitKey(1)

        saved = 0
        next_save = time.time()

        while saved < args.samples:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            crop, box = crop_center(frame, nav_top, center_range)
            x1, y1, x2, y2 = box
            display = frame.copy()

            cv2.rectangle(
                display, (x1, y1), (x2 - 1, y2 - 1),
                (255, 255, 255), 3
            )

            cv2.putText(
                display,
                f"CENTER -> {args.label} | {saved}/{args.samples}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )

            cv2.imshow("Atlas CENTER Collector", display)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                print("User cancelled.")
                break

            now = time.time()
            if now < next_save:
                continue

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            prepared = letterbox_square(crop, IMGSZ)
            prepared_name = f"center_{args.label}_{stamp}.jpg"
            evidence_name = f"center_{args.label}_{stamp}_evidence.jpg"

            save_jpg(dataset_dir / prepared_name, prepared)
            save_jpg(evidence_dir / evidence_name, display)

            saved += 1
            next_save = now + args.interval

            print(
                f"SAVED {saved:02d}/{args.samples} | "
                f"{args.split} | CENTER | {args.label}"
            )

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print()
    print("=" * 86)
    print("COLLECTION COMPLETE")
    print("=" * 86)
    print(f"Dataset  : {dataset_dir}")
    print(f"Evidence : {evidence_dir}")


if __name__ == "__main__":
    main()
