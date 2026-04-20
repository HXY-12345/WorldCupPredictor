"""核心功能：提供触发赛程刷新与同步流水线的接口。"""

from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.services.refresh import RefreshPipeline, run_refresh


def create_refresh_router(
    session_factory: Callable[[], Session],
    fixture_seed_path: str | None,
    refresh_pipeline: RefreshPipeline | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/refresh")
    def refresh_matches() -> JSONResponse:
        sync_run = run_refresh(
            session_factory=session_factory,
            fixture_seed_path=fixture_seed_path,
            refresh_pipeline=refresh_pipeline,
        )
        return JSONResponse(
            status_code=202,
            content={
                "sync_run_id": sync_run.id,
                "status": sync_run.status,
            },
        )

    return router
