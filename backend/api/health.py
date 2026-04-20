"""核心功能：提供后端服务的基础健康检查接口。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
