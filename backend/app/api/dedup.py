from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.dedup_service import cluster_scenes

router = APIRouter()


@router.post("/{video_id}")
async def deduplicate_video(video_id: int, db: AsyncSession = Depends(get_db)):
    n_clusters = await cluster_scenes(db, video_id=video_id)
    return {"video_id": video_id, "clusters": n_clusters}
