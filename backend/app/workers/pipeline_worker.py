from sqlalchemy import select
from ..database import AsyncSessionLocal
from ..models import Video, Job
from ..services import segmentation_service, embeddings_service, utility_service, dedup_service, optimization_service
from ..services.faiss_store import get_faiss_store


async def run_pipeline(video_id: int):
    async with AsyncSessionLocal() as db:
        job = Job(video_id=video_id, kind="pipeline", status="running")
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            await segmentation_service.segment_and_create_scenes(db, video_id)
            await embeddings_service.embed_scenes_for_video(db, video_id)
            await utility_service.score_scenes(db, video_id)
            await dedup_service.cluster_scenes(db, video_id=video_id)
            await optimization_service.select_clips(db, compression=0.5)

            job.status = "completed"
            video = await db.get(Video, video_id)
            if video:
                video.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.result = {"error": str(exc)}
            raise
        finally:
            await get_faiss_store().save()
            await db.commit()
