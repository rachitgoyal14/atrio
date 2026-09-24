import os
import cv2
import numpy as np
import json
from pathlib import Path
from .dicom_utils import decode_image_bytes

try:
    from core.config import settings
    ROI_DIR = settings.ROI_STORAGE_PATH
except Exception:
    ROI_DIR = str(Path(__file__).resolve().parents[2] / "storage" / "roi")

def extract_roi(image_bytes, yolo_out, filename, scale=2):
    os.makedirs(ROI_DIR, exist_ok=True)

    img = decode_image_bytes(image_bytes)
    if img is None:
        raise ValueError("extract_roi: undecodable image bytes")
    H, W = img.shape[:2]

    x1, y1, x2, y2 = map(int, yolo_out["box"])
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    bw, bh = int((x2 - x1) * scale), int((y2 - y1) * scale)
    # Ensure a minimum ROI size so tiny boxes still yield usable context
    bw = max(bw, 32)
    bh = max(bh, 32)

    x1p = max(0, cx - bw)
    y1p = max(0, cy - bh)
    x2p = min(W, cx + bw)
    y2p = min(H, cy + bh)

    roi = img[y1p:y2p, x1p:x2p]

    # YOLO box relative to ROI
    yolo_box_roi = [
        x1 - x1p,
        y1 - y1p,
        x2 - x1p,
        y2 - y1p
    ]

    safe_name = Path(filename).name
    roi_path = os.path.join(ROI_DIR, safe_name)
    cv2.imwrite(roi_path, roi)

    meta = {"yolo_box": yolo_box_roi}

    meta_path = os.path.join(ROI_DIR, safe_name + ".json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return roi, meta
