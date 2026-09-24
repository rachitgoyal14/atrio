import os
import cv2
import numpy as np
from pathlib import Path
from skimage.filters import frangi
from skimage.morphology import remove_small_objects

try:
    from core.config import settings
    MASKS_DIR = settings.MASKS_STORAGE_PATH
except Exception:
    MASKS_DIR = str(Path(__file__).resolve().parents[2] / "storage" / "masks")

def segment_lumen(roi, filename):
    os.makedirs(MASKS_DIR, exist_ok=True)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # frangi expects float in [0, 1]
    gray_f = gray.astype(np.float32) / 255.0
    vessel = frangi(gray_f)
    vmax = float(vessel.max())
    if not np.isfinite(vmax) or vmax <= 0:
        # No vessel response: return empty mask instead of crashing on div-by-zero
        mask = np.zeros_like(gray, dtype=np.uint8)
        cv2.imwrite(os.path.join(MASKS_DIR, Path(filename).name), mask)
        return mask
    vessel = (vessel / vmax * 255).astype(np.uint8)

    binary = cv2.adaptiveThreshold(
        vessel, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, -2
    )

    binary = remove_small_objects(binary > 0, min_size=150)
    mask = (binary * 255).astype(np.uint8)

    cv2.imwrite(os.path.join(MASKS_DIR, Path(filename).name), mask)
    return mask
