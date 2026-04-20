"""核心功能：提供赛后评估记录列表与单场详情查询接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.repositories.evaluations import MatchEvaluationRepository


def create_evaluations_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/evaluations")
    def list_evaluations() -> dict:
        with session_factory() as session:
            repository = MatchEvaluationRepository(session)
            return repository.list_payload()

    @router.get("/api/evaluations/{match_id}")
    def get_evaluation_detail(match_id: str) -> dict:
        with session_factory() as session:
            repository = MatchEvaluationRepository(session)
            payload = repository.get_detail_payload(match_id)
            if payload is None:
                raise HTTPException(status_code=404, detail=f"Evaluation for match '{match_id}' was not found.")
            return payload

    return router
