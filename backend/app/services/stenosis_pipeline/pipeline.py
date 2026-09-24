import os
import cv2
import uuid
import numpy as np
from pathlib import Path
from .yolo_service import detect_stenosis
from .dicom_utils import decode_image_bytes
from .roi_service import extract_roi
from .mask_service import segment_lumen
from .stenosis_service import compute_stenosis

try:
    from core.config import settings
    RESULTS_DIR = str(Path(settings.RESULTS_STORAGE_PATH) / "visuals")
    YOLO_RESULTS_DIR = str(Path(settings.RESULTS_STORAGE_PATH) / "yolo_detections")
except Exception:
    # Fallback when running outside app context (scripts/tests)
    APP_DIR = Path(__file__).resolve().parents[2]
    RESULTS_DIR = str(APP_DIR / "storage" / "results" / "visuals")
    YOLO_RESULTS_DIR = str(APP_DIR / "storage" / "results" / "yolo_detections")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(YOLO_RESULTS_DIR, exist_ok=True)


def run_stenosis_pipeline(image_bytes: bytes, image_name: str):
    """Full per-image pipeline: YOLO detect -> ROI -> lumen seg -> stenosis %.

    Accepts raw jpg/png bytes OR raw DICOM bytes. Returns None when no
    stenosis is detected (or image undecodable); otherwise a dict with
    artery / stenosis_percent / severity / confidence / visual paths
    (absolute filesystem paths; API layer converts these to /storage/... URLs).
    """
    yolo_out = detect_stenosis(image_bytes)

    # Decode once (handles jpg/png + DICOM); needed for the YOLO overlay visual
    full_img = decode_image_bytes(image_bytes)
    if full_img is None:
        return None

    yolo_vis_path = None

    if yolo_out["detected"]:
        x1, y1, x2, y2 = map(int, yolo_out["box"])
        # Guard against degenerate boxes
        h, w = full_img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            cv2.rectangle(full_img, (x1, y1), (x2, y2), (0, 0, 255), 3)

            yolo_vis_name = f"{uuid.uuid4()}_yolo.png"
            yolo_vis_path = os.path.join(YOLO_RESULTS_DIR, yolo_vis_name)
            cv2.imwrite(yolo_vis_path, full_img)

    if not yolo_out["detected"]:
        return None

    roi, meta = extract_roi(image_bytes, yolo_out, image_name)
    if roi is None or roi.size == 0:
        return None
    mask = segment_lumen(roi, image_name)
    result = compute_stenosis(roi, mask, meta)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    visual_name = f"{uuid.uuid4()}_visual.png"
    visual_path = os.path.join(RESULTS_DIR, visual_name)
    cv2.imwrite(visual_path, result["visual"])

    return {
        "artery": result["artery"],
        "stenosis_percent": result["percent"],
        "severity": result["severity"],
        "confidence": float(yolo_out["confidence"]),
        "visual_path": visual_path,
        "yolo_visual_path": yolo_vis_path,
    }
