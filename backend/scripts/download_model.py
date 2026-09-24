"""Download YOLO stenosis weights from Hugging Face (single source of truth).

Source: https://huggingface.co/rachitgoyell/stenosis-detection (file: best.pt)
Target: backend/ai_models/best.pt

Usage:
    python backend/scripts/download_model.py
    HF_MODEL_REPO=rachitgoyell/stenosis-detection HF_MODEL_FILE=best.pt python backend/scripts/download_model.py
"""
import os
import shutil
import sys
from pathlib import Path

REPO_ID = os.getenv("HF_MODEL_REPO", "rachitgoyell/stenosis-detection")
FILENAME = os.getenv("HF_MODEL_FILE", "best.pt")
TARGET = Path(__file__).resolve().parents[1] / "ai_models" / "best.pt"


def main() -> int:
    if TARGET.exists():
        print(f"OK: weights already present at {TARGET} ({TARGET.stat().st_size/1e6:.1f} MB)")
        return 0
    from huggingface_hub import hf_hub_download
    print(f"Downloading {REPO_ID}/{FILENAME} ...")
    cached = hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, TARGET)
    print(f"Saved -> {TARGET} ({TARGET.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
