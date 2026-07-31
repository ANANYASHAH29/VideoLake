from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Video
from ..services.ingestion_service import ingest_video
from ..workers.pipeline_worker import run_pipeline

router = APIRouter()


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    video = await ingest_video(file.file, file.filename, db)
    if background_tasks:
        background_tasks.add_task(run_pipeline, video.id)
    return {
        "video_id": video.id,
        "filename": video.filename,
        "duration_sec": video.duration_sec,
        "status": video.status,
    }


@router.get("/videos")
async def list_videos(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Video))).scalars().all()
    return [
        {
            "id": v.id,
            "filename": v.filename,
            "duration_sec": v.duration_sec,
            "status": v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in rows
    ]


@router.get("/videos/{video_id}")
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {
        "id": video.id,
        "filename": video.filename,
        "duration_sec": video.duration_sec,
        "status": video.status,
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }
