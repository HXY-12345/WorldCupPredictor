"""核心功能：提供预测成功率总览与按阶段聚合统计接口。"""

from collections.abc import Callable

from fastapi import APIRouter
from sqlalchemy.orm import Session

from backend.repositories.evaluations import MatchEvaluationRepository


def create_analytics_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/analytics/summary")
    def get_summary() -> dict:
        with session_factory() as session:
            repository = MatchEvaluationRepository(session)
            return repository.summary_payload()

    @router.get("/api/analytics/by-stage")
    def get_by_stage() -> dict:
        with session_factory() as session:
            repository = MatchEvaluationRepository(session)
            return repository.by_stage_payload()

    return router
