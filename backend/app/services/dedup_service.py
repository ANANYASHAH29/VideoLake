import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Scene
from .faiss_store import get_faiss_store
from ..config import settings


async def cluster_scenes(db: AsyncSession, video_id: int = None, eps: float = None, min_samples: int = 2) -> int:
    if eps is None:
        eps = settings.dedup_eps

    faiss = get_faiss_store()
    ids = faiss.all_ids()
    if len(ids) < 2:
        return 0

    # optionally restrict to a single video
    if video_id is not None:
        stmt = select(Scene.id).where(Scene.video_id == video_id)
        result = await db.execute(stmt)
        allowed = {r for r in result.scalars().all()}
        ids = [i for i in ids if i in allowed]

    if len(ids) < 2:
        return 0

    X = faiss.get_vectors(ids)
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(X)
    labels = clustering.labels_

    id_to_label = dict(zip(ids, labels.tolist()))
    stmt = select(Scene).where(Scene.id.in_(ids))
    scenes = (await db.execute(stmt)).scalars().all()
    for scene in scenes:
        scene.cluster_id = int(id_to_label.get(scene.id, -1))

    await db.commit()
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    return n_clusters
