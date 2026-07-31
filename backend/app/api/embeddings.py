from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Scene
from ..services.embeddings_service import extractor, embed_scenes_for_video
from ..services.faiss_store import get_faiss_store

router = APIRouter()


@router.post("/{video_id}")
async def embed_video(video_id: int, db: AsyncSession = Depends(get_db)):
    n = await embed_scenes_for_video(db, video_id)
    return {"video_id": video_id, "scenes_embedded": n}


@router.get("/search")
async def search_scenes(
    query: str = Query(..., description="Text query to search clips"),
    k: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    vec = extractor.encode_text(query)
    distances, indices = get_faiss_store().search(vec, k)
    results = []
    for d, i in zip(distances.tolist(), indices.tolist()):
        if i < 0:
            continue
        scene = await db.get(Scene, int(i))
        if scene:
            results.append(
                {
                    "scene_id": scene.id,
                    "video_id": scene.video_id,
                    "start_sec": scene.start_sec,
                    "end_sec": scene.end_sec,
                    "score": float(d),
                    "utility": scene.utility,
                }
            )
    return {"query": query, "results": results}
