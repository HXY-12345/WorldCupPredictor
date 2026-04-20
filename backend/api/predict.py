"""核心功能：提供单场比赛的手动预测生成接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.llm.provider import PredictionProvider, PredictionProviderError
from backend.services.prediction_guard import PredictionExecutionGuard
from backend.services.predictions import MatchNotPredictableError, MatchNotFoundError, create_prediction


def create_predict_router(
    session_factory: Callable[[], Session],
    prediction_provider: PredictionProvider | None = None,
    prediction_guard: PredictionExecutionGuard | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/predict/{match_id}")
    def predict_match(match_id: str) -> dict:
        guard_acquired = False
        try:
            if prediction_guard is not None:
                guard_acquired = prediction_guard.acquire(match_id)
                if not guard_acquired:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Prediction generation is already running for match '{match_id}'.",
                    )
            prediction = create_prediction(session_factory, match_id, provider=prediction_provider)
        except MatchNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except MatchNotPredictableError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except PredictionProviderError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        finally:
            if guard_acquired and prediction_guard is not None:
                prediction_guard.release(match_id)

        return {
            "match_id": match_id,
            "prediction": prediction,
            "cached": False,
        }

    return router
