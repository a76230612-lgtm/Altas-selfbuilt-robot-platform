import cv2
import hashlib
import shutil
import sys
from pathlib import Path
import numpy as np

TARGET_SIZE = 224
PAD_COLOR = (114, 114, 114)

DATASETS = {
    "EDGE": {
        "source": "Atlas_Edge_Dataset",
        "output": "Prepared_Atlas_Edge_Dataset",
        "classes": ["SAFE", "EDGE"],
    },
    "DIRECTIONAL": {
        "source": "Atlas_Directional_Dataset",
        "output": "Prepared_Atlas_Directional_Dataset",
        "classes": ["FREE", "BLOCKED"],
    },
}

SPLITS = ["train", "val", "test"]


def read_image_unicode_safe(path: Path):
    data = path.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def save_jpeg_unicode_safe(path: Path, image) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        return False
    encoded.tofile(str(path))
    return path.exists() and path.stat().st_size > 0


def letterbox_square(image, size=TARGET_SIZE):
    h, w = image.shape[:2]
    if h <= 0 or w <= 0:
        raise ValueError("Invalid image dimensions")

    scale = min(size / w, size / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR

    resized = cv2.resize(image, (new_w, new_h), interpolation=interp)

    pad_left = (size - new_w) // 2
    pad_right = size - new_w - pad_left
    pad_top = (size - new_h) // 2
    pad_bottom = size - new_h - pad_top

    return cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=PAD_COLOR,
    )


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_hashes(root: Path, split: str):
    result = {}
    split_dir = root / split
    if not split_dir.exists():
        return result

    for path in split_dir.rglob("*.jpg"):
        result.setdefault(sha256_file(path), []).append(path)

    return result


def prepare_dataset(base_dir: Path, dataset_name: str, spec: dict):
    source_root = base_dir / spec["source"]
    output_root = base_dir / spec["output"]

    print()
    print("=" * 78)
    print(f"{dataset_name} DATASET")
    print("=" * 78)
    print(f"Source : {source_root}")
    print(f"Output : {output_root}")

    if not source_root.exists():
        print("STATUS : FAIL")
        print("Reason : source dataset folder does not exist.")
        return False

    if output_root.exists():
        shutil.rmtree(output_root)

    total_source = 0
    total_saved = 0
    unreadable = []

    for split in SPLITS:
        for class_name in spec["classes"]:
            source_dir = source_root / split / class_name
            output_dir = output_root / split / class_name
            output_dir.mkdir(parents=True, exist_ok=True)

            if not source_dir.exists():
                print(f"WARNING: missing folder: {source_dir}")
                continue

            images = sorted(source_dir.glob("*.jpg"))
            print(f"{split:5s} / {class_name:9s}: {len(images):4d} source images")

            for image_path in images:
                total_source += 1

                try:
                    image = read_image_unicode_safe(image_path)
                except Exception:
                    image = None

                if image is None:
                    unreadable.append(image_path)
                    continue

                prepared = letterbox_square(image)
                output_path = output_dir / image_path.name

                if save_jpeg_unicode_safe(output_path, prepared):
                    total_saved += 1
                else:
                    unreadable.append(image_path)

    print()
    print(f"Readable/source images : {total_source - len(unreadable)}/{total_source}")
    print(f"Prepared images        : {total_saved}/{total_source}")

    if unreadable:
        print()
        print("UNREADABLE / SAVE-FAILED FILES:")
        for path in unreadable[:20]:
            print(f"  {path}")
        if len(unreadable) > 20:
            print(f"  ... plus {len(unreadable) - 20} more")

    train_hashes = collect_hashes(output_root, "train")
    val_hashes = collect_hashes(output_root, "val")
    overlap = sorted(set(train_hashes).intersection(val_hashes))

    print()
    if overlap:
        print(f"WARNING: {len(overlap)} exact image duplicate(s) appear in BOTH train and val.")
        print("Do not train until these are removed or re-collected.")
    else:
        print("Train/val exact duplicate check : PASS")

    success = (
        total_source > 0
        and total_saved == total_source
        and len(unreadable) == 0
        and len(overlap) == 0
    )

    print()
    print(f"PREPARE {dataset_name}: {'PASS' if success else 'CHECK REQUIRED'}")
    return success


def main():
    base_dir = Path(__file__).resolve().parent

    print("=" * 78)
    print("Atlas 6.0 - Training Data Preflight & Preparation")
    print("=" * 78)
    print(f"Working folder : {base_dir}")
    print(f"Target size    : {TARGET_SIZE} x {TARGET_SIZE}")
    print("Method         : letterbox (preserve complete field of view)")
    print()

    all_pass = True

    for dataset_name, spec in DATASETS.items():
        if not prepare_dataset(base_dir, dataset_name, spec):
            all_pass = False

    print()
    print("=" * 78)

    if all_pass:
        print("FINAL PREFLIGHT: PASS")
        print("Use these folders for training:")
        print("  Prepared_Atlas_Edge_Dataset")
        print("  Prepared_Atlas_Directional_Dataset")
        sys.exit(0)

    print("FINAL PREFLIGHT: CHECK REQUIRED")
    print("Do not start training until the reported issue is fixed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
