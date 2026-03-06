from fastapi import APIRouter

from core.response import success

router = APIRouter()


@router.get("/health", summary="Health Check", tags=["health"])
async def health_check():
    return success(data={"status": "ok"})