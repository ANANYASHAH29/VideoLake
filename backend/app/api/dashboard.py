import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Video, Scene

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_videos = (await db.execute(select(func.count(Video.id)))).scalar() or 0
    total_scenes = (await db.execute(select(func.count(Scene.id)))).scalar() or 0
    selected_scenes = (
        await db.execute(select(func.count(Scene.id)).where(Scene.selected == True))
    ).scalar() or 0

    status_counts = {
        row[0]: row[1]
        for row in (
            await db.execute(select(Video.status, func.count(Video.id)).group_by(Video.status))
        ).all()
    }

    total_duration = (
        await db.execute(select(func.sum(Scene.duration)))
    ).scalar() or 0.0
    selected_duration = (
        await db.execute(select(func.sum(Scene.duration)).where(Scene.selected == True))
    ).scalar() or 0.0

    return {
        "videos": total_videos,
        "scenes": total_scenes,
        "selected_scenes": selected_scenes,
        "status_counts": status_counts,
        "total_duration_sec": float(total_duration),
        "selected_duration_sec": float(selected_duration),
        "duration_reduction": 1.0 - selected_duration / max(1.0, total_duration),
    }


@router.get("/histogram")
async def utility_histogram(db: AsyncSession = Depends(get_db), bins: int = Query(20, ge=5, le=50)):
    utilities = (
        await db.execute(select(Scene.utility))
    ).scalars().all()
    utilities = [u for u in utilities if u is not None]
    if not utilities:
        return {"bins": [], "counts": []}
    counts, edges = np.histogram(utilities, bins=bins, range=(0.0, 1.0))
    return {
        "bins": [round(float(x), 3) for x in edges.tolist()],
        "counts": counts.tolist(),
    }


@router.get("/clusters")
async def cluster_summary(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Scene.cluster_id, func.count(Scene.id))
            .where(Scene.cluster_id != None)
            .group_by(Scene.cluster_id)
        )
    ).all()
    return {
        "clusters": len(rows),
        "cluster_sizes": {int(cid): count for cid, count in rows if cid is not None},
    }


@router.get("/topclips")
async def top_clips(db: AsyncSession = Depends(get_db), limit: int = Query(20, ge=1, le=100)):
    rows = (
        await db.execute(
            select(Scene).order_by(Scene.utility.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": s.id,
            "video_id": s.video_id,
            "start_sec": s.start_sec,
            "end_sec": s.end_sec,
            "utility": s.utility,
            "selected": s.selected,
        }
        for s in rows
    ]


@router.get("/reduction")
async def reduction_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Scene.id)))).scalar() or 0
    selected = (
        await db.execute(select(func.count(Scene.id)).where(Scene.selected == True))
    ).scalar() or 0
    return {
        "total_scenes": total,
        "selected_scenes": selected,
        "reduction": 1.0 - selected / max(1, total),
    }
