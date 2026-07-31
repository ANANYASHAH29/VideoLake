import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict

from ..config import settings


class FAISSStore:
    """Singleton FAISS store for scene embeddings."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, dim: int = 512):
        if not hasattr(self, "initialized"):
            self.dim = dim
            self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
            self.vectors: Dict[int, np.ndarray] = {}
            self.initialized = True

    def load(self):
        dir_path = Path(settings.faiss_index_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        idx_path = dir_path / "scenes.index"
        vec_path = dir_path / "vectors.npz"
        if idx_path.exists() and vec_path.exists():
            self.index = faiss.read_index(str(idx_path))
            loaded = np.load(vec_path)
            self.vectors = {int(k): loaded[k] for k in loaded.files}
            self.dim = self.index.d
        else:
            self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))

    def save(self):
        if self.index is None:
            return
        dir_path = Path(settings.faiss_index_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(dir_path / "scenes.index"))
        if self.vectors:
            np.savez(str(dir_path / "vectors.npz"), **{str(k): v for k, v in self.vectors.items()})

    def add(self, id: int, vector: np.ndarray):
        vector = vector.astype("float32").reshape(1, -1)
        faiss.normalize_L2(vector)
        self.index.add_with_ids(vector, np.array([id], dtype=np.int64))
        self.vectors[id] = vector[0]

    def search(self, vector: np.ndarray, k: int):
        q = vector.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)
        distances, indices = self.index.search(q, k)
        return distances[0], indices[0]

    def get_vector(self, id: int):
        return self.vectors.get(id)

    def get_vectors(self, ids: List[int]):
        if not ids:
            return np.zeros((0, self.dim), dtype="float32")
        return np.vstack([self.vectors[i] for i in ids])

    def all_ids(self) -> List[int]:
        return list(self.vectors.keys())


def get_faiss_store() -> FAISSStore:
    return FAISSStore()
