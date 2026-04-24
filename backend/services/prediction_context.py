"""核心功能：从比赛事实中组装预测智能体输入上下文。"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from backend.models.match import Match


@dataclass(frozen=True)
class PredictionContext:
    """预测智能体输入上下文。"""

    match_facts: dict[str, Any]
    database_context: dict[str, Any]


def build_prediction_context(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    recent_prediction_limit: int = 3,
    database_context: dict[str, Any] | None = None,
) -> PredictionContext:
    """从数据库构建仅包含比赛事实的预测上下文。"""

    _ = recent_prediction_limit

    with session_factory() as session:
        match = session.get(Match, match_id)
        if match is None:
            raise KeyError(f"Match '{match_id}' was not found.")

        return PredictionContext(
            match_facts=_serialize_match(match),
            database_context=deepcopy(database_context) if isinstance(database_context, dict) else {},
        )


def _serialize_match(match: Match) -> dict[str, Any]:
    return {
        "match_id": match.id,
        "official_match_number": match.official_match_number,
        "kickoff_label": match.kickoff_label,
        "sort_order": match.sort_order,
        "date": match.date,
        "time": match.time,
        "stage": match.stage,
        "group_name": match.group_name,
        "venue": match.venue,
        "home_team": deepcopy(match.home_team),
        "away_team": deepcopy(match.away_team),
        "status": match.status,
        "score": deepcopy(match.score),
    }
