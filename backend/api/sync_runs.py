"""核心功能：提供同步任务列表与任务详情查询接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.repositories.sync_runs import SyncRunRepository


def create_sync_runs_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/sync-runs")
    def list_sync_runs() -> dict:
        with session_factory() as session:
            repository = SyncRunRepository(session)
            return repository.list_payload()

    @router.get("/api/sync-runs/{sync_run_id}")
    def get_sync_run_detail(sync_run_id: str) -> dict:
        with session_factory() as session:
            repository = SyncRunRepository(session)
            payload = repository.get_detail_payload(sync_run_id)
            if payload is None:
                raise HTTPException(status_code=404, detail=f"Sync run '{sync_run_id}' was not found.")
            return payload

    return router
