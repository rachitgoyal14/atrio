import numpy as np
import cv2
from skimage.morphology import skeletonize
from scipy.ndimage import distance_transform_edt
from .artery_vision_service import detect_artery_name

def compute_stenosis(roi, mask, meta):
    binary = mask > 0
    skeleton = skeletonize(binary)
    dist = distance_transform_edt(binary)

    coords = np.column_stack(np.where(skeleton))
    diameters = dist[skeleton] * 2

    sx1, sy1, sx2, sy2 = meta["yolo_box"]

    inside = (
        (coords[:,1] >= sx1) & (coords[:,1] <= sx2) &
        (coords[:,0] >= sy1) & (coords[:,0] <= sy2)
    )
    outside = ~inside

    if inside.sum() < 3 or outside.sum() < 7:
        return {
            "percent": None,
            "severity": "Unreliable",
            "artery": "Unknown",
            "visual": roi
        }

    D_min = diameters[inside].min()
    D_ref = np.sort(diameters[outside])[-10:].mean()
    if not np.isfinite(D_ref) or D_ref <= 0:
        return {
            "percent": None,
            "severity": "Unreliable",
            "artery": "Unknown",
            "visual": roi
        }
    percent = float((1 - D_min / D_ref) * 100)
    # Clip measurement noise (D_min > D_ref can give small negatives)
    percent = max(0.0, min(100.0, percent))

    if percent < 30:
        severity = "Normal"
    elif percent < 50:
        severity = "Mild"
    elif percent < 70:
        severity = "Moderate"
    else:
        severity = "Severe"

    # ---------- Visualization ----------
    vis = roi.copy()

    cv2.rectangle(vis, (sx1, sy1), (sx2, sy2), (255, 0, 0), 2)

    idx_min = np.where(inside)[0][np.argmin(diameters[inside])]
    y_min, x_min = coords[idx_min]
    cv2.circle(vis, (x_min, y_min), 4, (0, 0, 255), -1)

    idx_ref = np.where(outside)[0][np.argmax(diameters[outside])]
    y_ref, x_ref = coords[idx_ref]
    cv2.circle(vis, (x_ref, y_ref), 4, (0, 255, 0), -1)

    cv2.putText(
        vis,
        f"{percent:.1f}%",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )

    # ---------- Azure OpenAI Vision ----------
    artery = detect_artery_name(vis)

    return {
        "percent": round(float(percent), 2),
        "severity": severity,
        "artery": artery,
        "visual": vis
    }
