from pydantic_settings import BaseSettings
from pathlib import Path

# backend/app/core/config.py -> parents: core(0) app(1) backend(2) atrio(3)
BASE_DIR = Path(__file__).resolve().parents[3]  # atrio/
APP_DIR = Path(__file__).resolve().parents[1]  # backend/app/

class Settings(BaseSettings):
    ENV: str = "dev"
    PROJECT_NAME: str = "Angio AI"
    # Default points at docker-compose postgres service; override in .env for local bare-metal
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/atrio"

    # Absolute storage paths so CWD never matters (local vs docker)
    DICOM_STORAGE_PATH: str = str(APP_DIR / "storage" / "dicom")
    REPORT_STORAGE_PATH: str = str(APP_DIR / "storage" / "reports")
    RESULTS_STORAGE_PATH: str = str(APP_DIR / "storage" / "results")
    ROI_STORAGE_PATH: str = str(APP_DIR / "storage" / "roi")
    MASKS_STORAGE_PATH: str = str(APP_DIR / "storage" / "masks")
    STORAGE_DIR: str = str(APP_DIR / "storage")

    model_config = {
        "env_file": ".env",
        "extra": "allow",   # ✅ THIS FIXES IT
    }

settings = Settings()

