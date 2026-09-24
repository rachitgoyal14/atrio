# ---- Atrio backend (FastAPI + YOLOv8 stenosis pipeline) ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # OpenCV runtime libs on slim images
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app/backend/app

# System libs: libgl1 + libglib2.0-0 for opencv, libgomp1 for torch/skimage
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install python deps first (better layer caching)
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# App code + model weights (weights also auto-download from HF on first run if absent)
COPY backend/app /app/backend/app
COPY backend/ai_models /app/backend/ai_models
COPY backend/scripts /app/backend/scripts
COPY backend/entrypoint.sh /app/backend/entrypoint.sh
RUN chmod +x /app/backend/entrypoint.sh

ENV PYTHONPATH=/app/backend/app \
    DATABASE_URL=postgresql://postgres:postgres@db:5432/atrio \
    HF_MODEL_REPO=rachitgoyell/stenosis-detection \
    HF_MODEL_FILE=best.pt \
    YOLO_CONF=0.25 \
    YOLO_IOU=0.45 \
    YOLO_IMGSZ=640

EXPOSE 8000

# Optional warm-up: pre-download weights at build time (fails open when offline)
RUN python /app/backend/scripts/download_model.py || echo "WARN: model download skipped (will retry at runtime)"

# On `docker compose up`, entrypoint downloads weights only if missing,
# otherwise reuses the already-downloaded file, then starts the API.
ENTRYPOINT ["/app/backend/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
