"""核心功能：承接 evidence 阶段输出，并在最终决策阶段落预测版本。"""

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from backend.llm.provider import PredictionProvider
from backend.services.predictions import CreatedPrediction, create_prediction_result


def decide_prediction(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    evidence_bundle: dict[str, Any],
    provider: PredictionProvider | None = None,
) -> CreatedPrediction:
    return create_prediction_result(
        session_factory,
        match_id,
        provider=provider,
        database_context={"evidence_bundle": evidence_bundle},
    )
