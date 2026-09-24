# app/main.py
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure `backend/app` is importable regardless of CWD (local run vs docker)
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from core.config import settings
from db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables + storage dirs on startup so a fresh clone just works
    await init_db()
    Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.DICOM_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.RESULTS_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.ROI_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.MASKS_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Angio AI Platform",
    description="AI-assisted angiography analysis & reporting",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(router)

app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","*"],  # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],   # VERY IMPORTANT
    allow_headers=["*"],
)
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "angio-ai",
        "env": settings.ENV
    }
