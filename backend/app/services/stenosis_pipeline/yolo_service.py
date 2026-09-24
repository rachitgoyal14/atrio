import os
from pathlib import Path

import cv2
import numpy as np
import torch

from .dicom_utils import decode_image_bytes

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = Path(os.getenv("YOLO_MODEL_PATH", str(BASE_DIR / "ai_models" / "best.pt")))

# Model source of truth (per model card):
# https://huggingface.co/rachitgoyell/stenosis-detection  (weights file: best.pt)
HF_REPO_ID = os.getenv("HF_MODEL_REPO", "rachitgoyell/stenosis-detection")
HF_FILENAME = os.getenv("HF_MODEL_FILE", "best.pt")

# Per model card: trained imgsz=640, conf threshold 0.25, IoU 0.45
YOLO_CONF = float(os.getenv("YOLO_CONF", "0.25"))
YOLO_IOU = float(os.getenv("YOLO_IOU", "0.45"))
YOLO_IMGSZ = int(os.getenv("YOLO_IMGSZ", "640"))

# ✅ Auto-select device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ✅ Lazy-load model so import never crashes (missing weights, no torch, etc.)
yolo_model = None
_yolo_error = None


def ensure_model_weights() -> Path | None:
    """Return local weights path, downloading from Hugging Face on first use."""
    if MODEL_PATH.exists():
        return MODEL_PATH
    try:
        from huggingface_hub import hf_hub_download
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        dl = hf_hub_download(repo_id=HF_REPO_ID, filename=HF_FILENAME)
        # Copy cached file to expected location for offline reuse
        import shutil
        shutil.copyfile(dl, MODEL_PATH)
        return MODEL_PATH
    except Exception as e:
        global _yolo_error
        _yolo_error = f"Model download failed ({HF_REPO_ID}/{HF_FILENAME}): {e}"
        return None


def _get_model():
    global yolo_model, _yolo_error
    if yolo_model is not None:
        return yolo_model
    try:
        weights = ensure_model_weights()
        if weights is None or not Path(weights).exists():
            _yolo_error = _yolo_error or f"Model weights not found at {MODEL_PATH}"
            return None
        from ultralytics import YOLO
        m = YOLO(str(weights))
        try:
            m.to(DEVICE)
        except Exception:
            pass
        yolo_model = m
        return yolo_model
    except Exception as e:  # pragma: no cover - hardware dependent
        _yolo_error = str(e)
        return None


def detect_stenosis(image_bytes):
    """Run YOLO stenosis detection.

    Returns {"detected": bool, "box": [x1,y1,x2,y2], "confidence": float, "shape": tuple}
    Picks the highest-confidence box (most likely culprit lesion).
    Handles both plain image bytes and raw DICOM bytes.
    """
    model = _get_model()
    if model is None:
        return {"detected": False, "reason": _yolo_error or "model unavailable"}

    img = decode_image_bytes(image_bytes)
    if img is None:
        return {"detected": False, "reason": "undecodable image (not jpg/png/dicom)"}

    # ✅ DO NOT pass device here (ultralytics handles it); imgsz/conf/iou per model card
    results = model(img, conf=YOLO_CONF, iou=YOLO_IOU, imgsz=YOLO_IMGSZ, verbose=False)

    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return {"detected": False}

    boxes = results[0].boxes
    confs = boxes.conf.cpu().numpy()
    best = int(np.argmax(confs))
    box = boxes.xyxy[best].cpu().numpy()
    conf = float(confs[best])

    # Clamp box to image bounds
    h, w = img.shape[:2]
    x1, y1, x2, y2 = [float(v) for v in box]
    x1, y1 = max(0.0, x1), max(0.0, y1)
    x2, y2 = min(float(w), x2), min(float(h), y2)

    return {
        "detected": True,
        "box": np.array([x1, y1, x2, y2], dtype=np.float32),
        "confidence": conf,
        "shape": img.shape,
    }
