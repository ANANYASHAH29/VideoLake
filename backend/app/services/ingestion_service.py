import shutil
import cv2
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Video, Job
from ..config import settings


def get_video_duration(path: str) -> float:
    cap = cv2.VideoCapture(path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps and fps > 0 and frames and frames > 0:
            return float(frames / fps)
    finally:
        cap.release()
    return 0.0


async def ingest_video(file_obj, filename: str, db: AsyncSession) -> Video:
    storage = Path(settings.video_storage)
    storage.mkdir(parents=True, exist_ok=True)
    dest = storage / filename

    # avoid collisions
    counter = 0
    original = dest
    while dest.exists():
        counter += 1
        dest = storage / f"{original.stem}_{counter}{original.suffix}"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file_obj, f)

    duration = get_video_duration(str(dest))
    video = Video(
        filename=dest.name,
        path=str(dest),
        duration_sec=duration,
        status="uploaded",
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    job = Job(video_id=video.id, kind="ingest", status="completed", result={"path": str(dest)})
    db.add(job)
    await db.commit()
    return video
