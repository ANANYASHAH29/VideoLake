import random
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Scene
from ..services.optimization_service import select_clips

router = APIRouter()


class EvaluateRequest(BaseModel):
    compression: float = Field(0.5, ge=0.0, le=0.99)


def _metrics(selection_ids, scenes, scene_map):
    if not selection_ids:
        return {}
    selected_scenes = [scene_map[sid] for sid in selection_ids]
    top_utility = sorted(scenes, key=lambda x: x.utility, reverse=True)[
        : max(1, int(0.2 * len(scenes)))
    ]
    top_ids = {s.id for s in top_utility}
    return {
        "data_reduction": 1.0 - len(selection_ids) / len(scenes),
        "selected": len(selection_ids),
        "avg_utility": float(np.mean([s.utility for s in selected_scenes])),
        "diversity_retention": float(np.mean([s.diversity for s in selected_scenes])),
        "novelty_retention": float(np.mean([s.novelty for s in selected_scenes])),
        "retrieval_recall": len(top_ids.intersection(set(selection_ids))) / len(top_ids)
        if top_ids
        else 0.0,
    }


@router.post("/evaluate/{video_id}")
async def evaluate_baselines(
    video_id: int,
    request: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(select(Scene).where(Scene.video_id == video_id))
    ).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No scenes found for this video")

    scenes = list(rows)
    scene_map = {s.id: s for s in scenes}
    target = max(1, int(len(scenes) * (1 - request.compression)))

    # Proposed utility selection
    await select_clips(db, compression=request.compression, video_id=video_id)
    for s in scenes:
        await db.refresh(s, ["selected"])
    proposed = [s.id for s in scenes if s.selected]

    # Baseline A: full dataset
    full = [s.id for s in scenes]

    # Baseline B: random
    random_sel = [s.id for s in random.sample(scenes, target)]

    # Baseline C: quality-only
    quality_sel = [
        s.id
        for s in sorted(scenes, key=lambda x: x.visual_quality, reverse=True)[:target]
    ]

    # Baseline D: dedup-only (one per cluster, then random fill)
    clusters = {}
    for s in scenes:
        clusters.setdefault(s.cluster_id, []).append(s)
    dedup = []
    for group in clusters.values():
        if group:
            dedup.append(max(group, key=lambda x: x.utility).id)
    if len(dedup) < target:
        remaining = [s.id for s in scenes if s.id not in dedup]
        extra = random.sample(remaining, min(target - len(dedup), len(remaining)))
        dedup.extend(extra)

    result = {
        "video_id": video_id,
        "compression": request.compression,
        "baselines": {
            "full_dataset": _metrics(full, scenes, scene_map),
            "random": _metrics(random_sel, scenes, scene_map),
            "quality_only": _metrics(quality_sel, scenes, scene_map),
            "dedup_only": _metrics(dedup, scenes, scene_map),
            "proposed_utility": _metrics(proposed, scenes, scene_map),
        },
    }
    return result
