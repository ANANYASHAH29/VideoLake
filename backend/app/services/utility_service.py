import cv2
import numpy as np
import torch
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers.util import pytorch_cos_sim

from ..models import Video, Scene
from ..config import settings
from .embeddings_service import extractor, sample_pil_at
from .faiss_store import get_faiss_store


CANDIDATE_LABELS = [
    "person", "people", "crowd", "animal", "dog", "cat", "bird", "horse", "car", "truck",
    "bicycle", "motorcycle", "bus", "train", "airplane", "boat", "building", "house", "skyscraper",
    "street", "road", "intersection", "bridge", "tunnel", "forest", "tree", "mountain", "beach",
    "ocean", "lake", "river", "waterfall", "desert", "snow", "grass", "flower", "garden",
    "kitchen", "bedroom", "living room", "office", "classroom", "hospital", "restaurant", "shop",
    "stadium", "stage", "concert", "festival", "wedding", "birthday", "meeting", "presentation",
    "sports", "running", "walking", "dancing", "cooking", "eating", "shopping", "driving", "flying",
    "surgery", "construction", "factory", "robots", "fire", "smoke", "rain", "snowing", "fog",
    "sunset", "sunrise", "night", "city lights", "fireworks", "market", "parade", "protest",
    "speech", "interview", "music", "art", "sculpture", "painting", "text", "screen", "map",
]


def normalize(values: List[float]) -> List[float]:
    arr = np.asarray(values, dtype=float)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-8:
        return [0.5 for _ in values]
    return ((arr - mn) / (mx - mn)).tolist()


def motion_for_scene(path: str, start: float, end: float, samples: int = 5) -> float:
    cap = cv2.VideoCapture(path)
    flows = []
    prev = None
    try:
        for t in np.linspace(start, end, samples):
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev is not None:
                flow = cv2.calcOpticalFlowFarneback(prev, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
                flows.append(np.var(mag))
            prev = gray
    finally:
        cap.release()
    return float(np.mean(flows)) if flows else 0.0


def visual_quality_for_scene(path: str, start: float, end: float, samples: int = 5) -> float:
    cap = cv2.VideoCapture(path)
    scores = []
    try:
        for t in np.linspace(start, end, samples):
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_64F).var()
            _, std = cv2.meanStdDev(gray)
            std = float(std[0][0])
            if std < 1:
                std = 1
            score = min(1.0, lap / 1000.0) * (std / 128.0)
            scores.append(min(1.0, score))
    finally:
        cap.release()
    return float(np.mean(scores)) if scores else 0.0


def caption_alignment_for_scene(path: str, start: float, end: float) -> float:
    mid = (start + end) / 2
    img = sample_pil_at(path, mid)
    if img is None:
        return 0.0
    texts = [f"a photo of {label}" for label in CANDIDATE_LABELS]
    img_vec = extractor.encode_image(img)
    text_vecs = extractor.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    sims = pytorch_cos_sim(torch.tensor(img_vec), torch.tensor(text_vecs))[0]
    top5 = sims.topk(5).values.detach().cpu().numpy()
    return float(np.mean(top5))


async def score_scenes(db: AsyncSession, video_id: int) -> List[Scene]:
    video = (await db.execute(select(Video).where(Video.id == video_id))).scalar_one_or_none()
    if not video:
        raise ValueError(f"Video {video_id} not found")

    scenes = (await db.execute(select(Scene).where(Scene.video_id == video_id))).scalars().all()
    if not scenes:
        return []

    faiss = get_faiss_store()
    raw_div, raw_nov, raw_cap, raw_mot, raw_vis = [], [], [], [], []

    for scene in scenes:
        vec = faiss.get_vector(scene.id)
        if vec is None:
            raw_div.append(0.0)
            raw_nov.append(0.0)
            raw_cap.append(0.0)
            raw_mot.append(0.0)
            raw_vis.append(0.0)
            continue

        distances, indices = faiss.search(vec, settings.utility_k_neighbours + 1)
        sims = [d for d, i in zip(distances.tolist(), indices.tolist()) if i != scene.id]
        if not sims:
            sims = distances.tolist()[1:] if len(distances) > 1 else [0.0]

        mean_sim = float(np.mean(sims[: settings.utility_k_neighbours]))
        max_sim = float(np.max(sims[: settings.utility_k_neighbours]) if sims else 0.0)

        raw_div.append(1.0 - mean_sim)
        raw_nov.append(1.0 - max_sim)
        raw_cap.append(caption_alignment_for_scene(video.path, scene.start_sec, scene.end_sec))
        raw_mot.append(motion_for_scene(video.path, scene.start_sec, scene.end_sec))
        raw_vis.append(visual_quality_for_scene(video.path, scene.start_sec, scene.end_sec))

    norm_div = normalize(raw_div)
    norm_nov = normalize(raw_nov)
    norm_cap = normalize(raw_cap)
    norm_mot = normalize(raw_mot)
    norm_vis = normalize(raw_vis)

    for i, scene in enumerate(scenes):
        scene.diversity = norm_div[i]
        scene.novelty = norm_nov[i]
        scene.caption_alignment = norm_cap[i]
        scene.motion_complexity = norm_mot[i]
        scene.visual_quality = norm_vis[i]
        scene.utility = (
            0.30 * scene.diversity
            + 0.25 * scene.novelty
            + 0.20 * scene.caption_alignment
            + 0.15 * scene.motion_complexity
            + 0.10 * scene.visual_quality
        )

    await db.commit()
    video.status = "scored"
    await db.commit()
    await faiss.save()
    return scenes
