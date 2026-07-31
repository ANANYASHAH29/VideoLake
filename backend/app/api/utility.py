from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Scene
from ..services.utility_service import score_scenes

router = APIRouter()


@router.post("/score/{video_id}")
async def score_video(video_id: int, db: AsyncSession = Depends(get_db)):
    scenes = await score_scenes(db, video_id)
    return {"video_id": video_id, "scenes_scored": len(scenes)}


@router.get("/scores/{video_id}")
async def get_scores(video_id: int, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(Scene).where(Scene.video_id == video_id))
    ).scalars().all()
    return [
        {
            "id": s.id,
            "start_sec": s.start_sec,
            "end_sec": s.end_sec,
            "diversity": s.diversity,
            "novelty": s.novelty,
            "caption_alignment": s.caption_alignment,
            "motion_complexity": s.motion_complexity,
            "visual_quality": s.visual_quality,
            "utility": s.utility,
        }
        for s in rows
    ]
