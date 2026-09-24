#!/bin/sh
# Atrio backend entrypoint: ensure YOLO weights exist before serving.
# - If /app/backend/ai_models/best.pt already exists -> reuse it, no download.
# - Else download once from Hugging Face (rachitgoyell/stenosis-detection).
# - Never block startup: if the download fails (offline), the API still boots
#   and inference gracefully reports "no detections" until weights arrive.
set -eu

WEIGHTS_PATH="${YOLO_MODEL_PATH:-/app/backend/ai_models/best.pt}"

if [ -f "$WEIGHTS_PATH" ]; then
  echo "Model weights present at $WEIGHTS_PATH ($(du -h "$WEIGHTS_PATH" | cut -f1)) - skipping download."
else
  echo "Model weights not found at $WEIGHTS_PATH - downloading from ${HF_MODEL_REPO:-rachitgoyell/stenosis-detection}/${HF_MODEL_FILE:-best.pt} ..."
  python /app/backend/scripts/download_model.py || echo "WARN: model download failed - backend will start anyway (inference disabled until weights are available)."
fi

exec "$@"
