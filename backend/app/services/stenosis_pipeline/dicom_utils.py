"""Shared image decoding: regular image bytes AND DICOM bytes -> BGR uint8 ndarray."""
import io
import numpy as np
import cv2


def decode_image_bytes(image_bytes: bytes):
    """Return BGR uint8 image or None if undecodable.

    1. Try OpenCV imdecode (jpg/png).
    2. Fall back to pydicom (single-frame + multi-frame cine -> middle frame,
       MONOCHROME1 inversion, modality rescale, min-max normalize to 0-255).
    """
    if not image_bytes:
        return None

    # --- 1. plain image ---
    try:
        img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except Exception:
        pass

    # --- 2. DICOM ---
    try:
        import pydicom
    except ImportError:
        return None
    try:
        ds = pydicom.dcmread(io.BytesIO(image_bytes), force=True)
        if not hasattr(ds, "pixel_array"):
            return None
        arr = ds.pixel_array

        # Multi-frame (cine): (frames, H, W) -> middle frame
        if arr.ndim == 4:  # (frames, H, W, C)
            arr = arr[arr.shape[0] // 2]
        elif arr.ndim == 3 and getattr(ds, "NumberOfFrames", 1) not in (None, 1):
            # (frames, H, W) grayscale cine
            try:
                n = int(ds.NumberOfFrames)
                if arr.shape[0] == n:
                    arr = arr[n // 2]
            except Exception:
                pass

        # Apply rescale if present
        try:
            slope = float(getattr(ds, "RescaleSlope", 1) or 1)
            intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
            if slope != 1 or intercept != 0:
                arr = arr.astype(np.float32) * slope + intercept
        except Exception:
            pass

        arr = np.asarray(arr, dtype=np.float32)

        # MONOCHROME1: low values = white -> invert to MONOCHROME2 convention
        try:
            if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
                arr = arr.max() - arr
        except Exception:
            pass

        lo, hi = float(arr.min()), float(arr.max())
        if hi <= lo:
            return None
        norm = ((arr - lo) / (hi - lo) * 255.0).clip(0, 255).astype(np.uint8)

        if norm.ndim == 2:
            return cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
        if norm.shape[2] == 3:
            # DICOM RGB -> OpenCV BGR
            return norm[:, :, ::-1].copy()
        if norm.shape[2] == 4:
            return cv2.cvtColor(norm, cv2.COLOR_RGBA2BGR)
        return norm
    except Exception:
        return None
