import faiss
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Scene
from .faiss_store import get_faiss_store
from ..config import settings


async def select_clips(
    db: AsyncSession,
    compression: float = 0.5,
    dedup_eps: float = None,
    video_id: int = None,
) -> list:
    if dedup_eps is None:
        dedup_eps = settings.dedup_eps

    stmt = select(Scene)
    if video_id is not None:
        stmt = stmt.where(Scene.video_id == video_id)
    scenes = (await db.execute(stmt)).scalars().all()
    if not scenes:
        return []

    # reset previous selection for the queried scope
    for s in scenes:
        s.selected = False
    await db.commit()

    # avoid selecting too many if compression is very low
    target = max(1, int(len(scenes) * (1 - compression)))
    sorted_scenes = sorted(scenes, key=lambda x: x.utility, reverse=True)

    faiss_store = get_faiss_store()
    dim = faiss_store.dim
    temp_index = faiss.IndexFlatIP(dim)
    selected = []

    for scene in sorted_scenes:
        if len(selected) >= target:
            break
        vec = faiss_store.get_vector(scene.id)
        if vec is None:
            continue
        q = vec.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)

        if temp_index.ntotal > 0:
            distances, _ = temp_index.search(q, 1)
            if distances[0][0] > 1.0 - dedup_eps:
                continue

        selected.append(scene)
        scene.selected = True
        temp_index.add(q)

    await db.commit()
    return selected
