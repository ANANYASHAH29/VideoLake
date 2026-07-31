from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/lv.db"
    video_storage: str = "./data/videos"
    faiss_index_dir: str = "./data/faiss"
    model_name: str = "clip-ViT-B-32"
    device: str = "cpu"
    utility_k_neighbours: int = 5
    dedup_eps: float = 0.15

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
