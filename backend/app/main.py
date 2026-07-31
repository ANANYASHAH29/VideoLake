import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add repo root to PYTHONPATH so backend can import research/ if needed
sys.path.insert(0, str(Path(__file__).parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .api import ingestion, segmentation, embeddings, utility, dedup, optimization, research, dashboard
from .services.faiss_store import get_faiss_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await get_faiss_store().load()
    yield
    await get_faiss_store().save()
    await engine.dispose()


app = FastAPI(
    title="LakeVideo",
    description="Curate hour-scale videos for foundation model training.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(segmentation.router, prefix="/api/segmentation", tags=["Segmentation"])
app.include_router(embeddings.router, prefix="/api/embeddings", tags=["Embeddings"])
app.include_router(utility.router, prefix="/api/utility", tags=["Utility"])
app.include_router(dedup.router, prefix="/api/dedup", tags=["Deduplication"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["Optimization"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok"}
