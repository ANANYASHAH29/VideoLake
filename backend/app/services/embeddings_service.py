import cv2
from typing import Optional, List
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from ..models import Video, Scene
from ..config import settings
from .faiss_store import get_faiss_store


class CLIPExtractor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        self.model = SentenceTransformer(settings.model_name, device=settings.device)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode_image(self, img: Image.Image):
        return self.model.encode(img, normalize_embeddings=True, show_progress_bar=False)

    def encode_images(self, images: List[Image.Image]):
        return self.model.encode(images, normalize_embeddings=True, show_progress_bar=False, batch_size=8)

    def encode_text(self, text: str):
        return self.model.encode(text, normalize_embeddings=True, show_progress_bar=False)


extractor = CLIPExtractor()


def sample_pil_at(path: str, sec: float) -> Optional[Image.Image]:
    cap = cv2.VideoCapture(path)
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ret, frame = cap.read()
        if not ret:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)
    finally:
        cap.release()


async def embed_scenes_for_video(db: AsyncSession, video_id: int) -> int:
    video = (await db.execute(select(Video).where(Video.id == video_id))).scalar_one_or_none()
    if not video:
        raise ValueError(f"Video {video_id} not found")

    scenes = (await db.execute(select(Scene).where(Scene.video_id == video_id))).scalars().all()
    faiss = get_faiss_store()

    for scene in scenes:
        path = scene.clip_path or video.path
        t = 0.5 if scene.clip_path and scene.duration > 0 else scene.start_sec + scene.duration / 2
        img = sample_pil_at(path, t)
        if img is None:
            continue
        vec = extractor.encode_image(img)
        faiss.add(scene.id, vec)
        scene.embedding_id = scene.id

    await db.commit()
    video.status = "embedded"
    await db.commit()
    await faiss.save()
    return len(scenes)
