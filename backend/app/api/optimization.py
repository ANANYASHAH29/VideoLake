from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.optimization_service import select_clips

router = APIRouter()


class OptimizeRequest(BaseModel):
    compression: float = Field(0.5, ge=0.0, le=0.99)


@router.post("/")
async def optimize_dataset(
    request: OptimizeRequest, db: AsyncSession = Depends(get_db)
):
    selected = await select_clips(db, compression=request.compression)
    total = await get_total_scenes(db)
    return {
        "selected": len(selected),
        "compression": request.compression,
        "total_scenes": total,
        "reduction": 1.0 - len(selected) / max(1, total),
    }


async def get_total_scenes(db: AsyncSession) -> int:
    from sqlalchemy import func
    from ..models import Scene
    return (await db.execute(func.count(Scene.id))).scalar() or 0
