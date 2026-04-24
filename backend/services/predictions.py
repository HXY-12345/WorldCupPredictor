"""核心功能：实现比赛预测校验、最终预测版本落库与最新摘要更新。"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.llm.openrouter_prediction import OpenRouterPredictionProvider
from backend.llm.provider import PredictionProvider, PredictionProviderConfigError
from backend.models.match import Match
from backend.models.prediction_version import PredictionVersion
from backend.services.prediction_context import build_prediction_context, PredictionContext
from backend.services.prediction_prompt import build_prediction_request
from backend.services.prediction_schema import parse_prediction_output


class MatchNotFoundError(Exception):
    pass


class MatchNotPredictableError(Exception):
    pass


@dataclass(frozen=True)
class CreatedPrediction:
    prediction: dict[str, Any]
    prediction_version_id: int
    prediction_version_no: int


def create_prediction(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    provider: PredictionProvider | None = None,
) -> dict[str, Any]:
    return create_prediction_result(
        session_factory,
        match_id,
        provider=provider,
    ).prediction


def create_prediction_result(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    provider: PredictionProvider | None = None,
    database_context: dict[str, Any] | None = None,
) -> CreatedPrediction:
    with session_factory() as session:
        match = session.get(Match, match_id)
        if match is None:
            raise MatchNotFoundError(f"Match '{match_id}' was not found.")
        if match.status != "not_started":
            raise MatchNotPredictableError("Predictions are only allowed before kickoff.")
        if provider is None:
            raise PredictionProviderConfigError("Prediction decider is not configured.")
        predicted_at = datetime.now(UTC).isoformat()

        next_version_no = (
            session.scalar(
                select(func.max(PredictionVersion.version_no)).where(
                    PredictionVersion.match_id == match_id
                )
            )
            or 0
        ) + 1

        prediction_context = build_prediction_context(
            session_factory,
            match_id,
            database_context=database_context,
        )
        prediction_request = _build_request_for_provider(prediction_context, provider)
        prediction_output = provider.predict(prediction_request)
        parsed_prediction = parse_prediction_output(prediction_output)
        prediction = parsed_prediction.model_dump(mode="json")
        prediction["model_meta"]["predicted_at"] = predicted_at
        prediction_version = PredictionVersion(
            match_id=match_id,
            version_no=next_version_no,
            created_at=predicted_at,
            model_name=prediction["model_meta"]["model_name"],
            prediction=prediction,
        )
        session.add(prediction_version)
        match.prediction = prediction
        session.add(match)
        session.commit()
        session.refresh(prediction_version)
        return CreatedPrediction(
            prediction=prediction,
            prediction_version_id=prediction_version.id,
            prediction_version_no=prediction_version.version_no,
        )


def _build_request_for_provider(
    prediction_context: PredictionContext,
    provider: PredictionProvider,
):
    if isinstance(provider, OpenRouterPredictionProvider):
        return build_prediction_request(
            prediction_context,
            enable_web_plugin=provider.settings.enable_web_plugin,
            enable_response_healing=provider.settings.enable_response_healing,
            require_parameters=provider.settings.require_parameters,
            use_response_format=False,
        )

    return build_prediction_request(prediction_context)
