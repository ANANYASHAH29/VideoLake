from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Scene
from ..services import segmentation_service

router = APIRouter()


@router.post("/{video_id}")
async def segment_video(video_id: int, db: AsyncSession = Depends(get_db)):
    scenes = await segmentation_service.segment_and_create_scenes(db, video_id)
    return {"video_id": video_id, "scenes_created": len(scenes)}


@router.get("/scenes/{video_id}")
async def get_scenes(video_id: int, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(Scene).where(Scene.video_id == video_id))
    ).scalars().all()
    return [
        {
            "id": s.id,
            "video_id": s.video_id,
            "start_sec": s.start_sec,
            "end_sec": s.end_sec,
            "duration": s.duration,
            "cluster_id": s.cluster_id,
            "utility": s.utility,
            "selected": s.selected,
        }
        for s in rows
    ]
