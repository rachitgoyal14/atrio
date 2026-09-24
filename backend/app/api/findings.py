from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pathlib import Path

from db.session import get_db
from models.image import Image
from models.finding import Finding

try:
    from core.config import settings
    _STORAGE_DIR = Path(settings.STORAGE_DIR).resolve()
except Exception:
    _STORAGE_DIR = (Path(__file__).resolve().parents[1] / "storage").resolve()


def _to_web_path(fs_path: str | None) -> str | None:
    """Convert absolute filesystem path under storage/ to /storage/... URL."""
    if not fs_path:
        return None
    p = str(fs_path).replace("\\", "/")
    try:
        rel = Path(fs_path).resolve().relative_to(_STORAGE_DIR)
        return f"/storage/{rel.as_posix()}"
    except Exception:
        # Already a web-style path, or legacy relative path like storage/...
        if p.startswith("/storage/"):
            return p
        if p.startswith("storage/"):
            return f"/{p}"
        return f"/{p.lstrip('/')}"

router = APIRouter(tags=["Findings"])

@router.get("/studies/{study_id}/findings-view")
async def findings_summary(
    study_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Image.id,
            Image.file_path,
            Finding.artery,
            Finding.blockage_pct,
            Finding.confidence,
            Finding.heatmap_path,
        )
        .join(Finding, Finding.image_id == Image.id)
        .where(Image.study_id == study_id)
    )

    rows = (await db.execute(stmt)).all()

    return {
        "study_id": str(study_id),
        "images": [
            {
                "image_id": str(r.id),
                "artery": r.artery,
                "blockage_pct": r.blockage_pct,
                "confidence": r.confidence,

                # 👇 THIS is the key part
                "image_path": _to_web_path(r.file_path),
                "heatmap_path": _to_web_path(r.heatmap_path),
            }
            for r in rows
        ],
    }
