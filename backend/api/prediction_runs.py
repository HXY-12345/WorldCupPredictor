"""核心功能：提供 prediction_runs 执行记录列表与详情查询接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.repositories.prediction_runs import PredictionRunRepository


def create_prediction_runs_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/matches/{match_id}/prediction-runs")
    def list_prediction_runs(match_id: str) -> dict:
        with session_factory() as session:
            repository = PredictionRunRepository(session)
            if not repository.match_exists(match_id):
                raise HTTPException(status_code=404, detail=f"Match '{match_id}' was not found.")
            return repository.list_payload(match_id)

    @router.get("/api/prediction-runs/{prediction_run_id}")
    def get_prediction_run_detail(prediction_run_id: str) -> dict:
        with session_factory() as session:
            repository = PredictionRunRepository(session)
            payload = repository.get_detail_payload(prediction_run_id)
            if payload is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Prediction run '{prediction_run_id}' was not found.",
                )
            return payload

    return router
