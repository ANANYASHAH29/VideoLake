import cv2
import subprocess
from pathlib import Path
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Video, Scene
from ..config import settings


def detect_scenes(path: str, threshold: float = 3000.0, min_scene_len: float = 2.0) -> List[Tuple[float, float]]:
    cap = cv2.VideoCapture(path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = total / fps if fps and total else 0.0
        boundaries = [0.0]
        prev_hist = None
        frame_no = 0
        sample = max(1, int(fps))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_no % sample == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
                if prev_hist is not None:
                    diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)
                    if diff > threshold:
                        t = frame_no / fps
                        if t - boundaries[-1] >= min_scene_len:
                            boundaries.append(t)
                prev_hist = hist
            frame_no += 1
    finally:
        cap.release()

    if not boundaries or duration - boundaries[-1] >= min_scene_len:
        boundaries.append(float(duration))

    return [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]


async def cut_clip(video_path: str, start: float, end: float, output: Path) -> bool:
    duration = end - start
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        video_path,
        "-t",
        str(duration),
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        str(output),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output.exists() and output.stat().st_size > 0
    except Exception:
        return False


async def segment_and_create_scenes(db: AsyncSession, video_id: int) -> List[Scene]:
    video = (await db.execute(select(Video).where(Video.id == video_id))).scalar_one_or_none()
    if not video:
        raise ValueError(f"Video {video_id} not found")

    pairs = detect_scenes(video.path)
    clip_dir = Path(settings.video_storage) / "clips" / str(video_id)
    clip_dir.mkdir(parents=True, exist_ok=True)

    scenes: List[Scene] = []
    for idx, (start, end) in enumerate(pairs):
        dur = end - start
        clip_path = clip_dir / f"scene_{idx:05d}.mp4"
        ok = await cut_clip(video.path, start, end, clip_path)
        scene = Scene(
            video_id=video.id,
            start_sec=start,
            end_sec=end,
            duration=dur,
            clip_path=str(clip_path) if ok else None,
            metadata_={"idx": idx},
        )
        db.add(scene)
        scenes.append(scene)

    await db.commit()
    for scene in scenes:
        await db.refresh(scene)

    video.status = "segmented"
    await db.commit()
    return scenes
