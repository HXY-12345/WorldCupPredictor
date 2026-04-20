"""核心功能：选择赛前最后一版预测并将赛后评估结果幂等写入数据库。"""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.evaluation.scorer import RULE_VERSION, score_prediction
from backend.models.match import Match
from backend.models.match_evaluation import MatchEvaluation
from backend.models.prediction_version import PredictionVersion

FINISHED_STATUSES = {"finished", "completed"}


class MatchEvaluationNotFoundError(Exception):
    pass


def evaluate_match(session_factory: sessionmaker[Session], match_id: str) -> dict[str, Any]:
    with session_factory() as session:
        match = session.get(Match, match_id)
        if match is None:
            raise MatchEvaluationNotFoundError(f"Match '{match_id}' was not found.")

        evaluation = session.scalar(
            select(MatchEvaluation).where(MatchEvaluation.match_id == match_id)
        )
        if evaluation is None:
            evaluation = MatchEvaluation(match_id=match_id)

        payload = _build_evaluation_payload(session, match)
        _apply_payload(evaluation, payload)
        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)
        return _serialize_evaluation(evaluation, match)


def evaluate_finished_matches(
    session_factory: sessionmaker[Session],
    *,
    match_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    with session_factory() as session:
        statement = select(Match.id).where(Match.status.in_(tuple(FINISHED_STATUSES)))
        if match_ids is not None:
            normalized_ids = list(dict.fromkeys(match_ids))
            if not normalized_ids:
                return []
            statement = statement.where(Match.id.in_(normalized_ids))
        statement = statement.order_by(Match.date.asc(), Match.sort_order.asc(), Match.id.asc())
        candidate_ids = session.scalars(statement).all()

    return [evaluate_match(session_factory, match_id) for match_id in candidate_ids]


def _build_evaluation_payload(session: Session, match: Match) -> dict[str, Any]:
    actual_score = _extract_actual_score(match)
    evaluated_at = datetime.now(UTC).isoformat()

    if actual_score is None:
        return {
            "prediction_version_id": None,
            "evaluation_status": "pending_result",
            "actual_home_score": None,
            "actual_away_score": None,
            "outcome_hit": None,
            "exact_score_hit": None,
            "home_goals_hit": None,
            "away_goals_hit": None,
            "total_goals_hit": None,
            "grade": None,
            "rule_version": RULE_VERSION,
            "evaluated_at": evaluated_at,
        }

    actual_home_score, actual_away_score = actual_score
    prediction_version = _select_official_prediction_version(session, match)
    if prediction_version is None:
        return {
            "prediction_version_id": None,
            "evaluation_status": "no_prediction",
            "actual_home_score": actual_home_score,
            "actual_away_score": actual_away_score,
            "outcome_hit": None,
            "exact_score_hit": None,
            "home_goals_hit": None,
            "away_goals_hit": None,
            "total_goals_hit": None,
            "grade": None,
            "rule_version": RULE_VERSION,
            "evaluated_at": evaluated_at,
        }

    scorecard = score_prediction(
        prediction_version.prediction,
        actual_home_score=actual_home_score,
        actual_away_score=actual_away_score,
    )
    return {
        "prediction_version_id": prediction_version.id,
        "evaluation_status": "scored",
        "actual_home_score": actual_home_score,
        "actual_away_score": actual_away_score,
        **scorecard,
        "rule_version": RULE_VERSION,
        "evaluated_at": evaluated_at,
    }


def _extract_actual_score(match: Match) -> tuple[int, int] | None:
    if (match.status or "").lower() not in FINISHED_STATUSES:
        return None

    score = match.score or {}
    home = score.get("home") if isinstance(score, dict) else None
    away = score.get("away") if isinstance(score, dict) else None
    if not isinstance(home, int) or not isinstance(away, int):
        return None

    return home, away


def _select_official_prediction_version(session: Session, match: Match) -> PredictionVersion | None:
    versions = session.scalars(
        select(PredictionVersion).where(PredictionVersion.match_id == match.id)
    ).all()
    if not versions:
        return None

    kickoff_at = _resolve_kickoff_datetime(match)
    eligible_versions = []
    for version in versions:
        created_at = _parse_datetime(version.created_at)
        if created_at is None:
            continue
        if kickoff_at is None or created_at < kickoff_at:
            eligible_versions.append((created_at, version.version_no, version.id, version))

    if not eligible_versions:
        return None

    eligible_versions.sort(reverse=True)
    return eligible_versions[0][3]


def _resolve_kickoff_datetime(match: Match) -> datetime | None:
    if not match.date:
        return None

    time_value = match.time or "23:59:59"
    if len(time_value) == 5:
        time_value = f"{time_value}:00"
    return _parse_datetime(f"{match.date}T{time_value}")


def _parse_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None

    normalized = raw_value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _apply_payload(evaluation: MatchEvaluation, payload: dict[str, Any]) -> None:
    evaluation.prediction_version_id = payload["prediction_version_id"]
    evaluation.evaluation_status = payload["evaluation_status"]
    evaluation.actual_home_score = payload["actual_home_score"]
    evaluation.actual_away_score = payload["actual_away_score"]
    evaluation.outcome_hit = payload["outcome_hit"]
    evaluation.exact_score_hit = payload["exact_score_hit"]
    evaluation.home_goals_hit = payload["home_goals_hit"]
    evaluation.away_goals_hit = payload["away_goals_hit"]
    evaluation.total_goals_hit = payload["total_goals_hit"]
    evaluation.grade = payload["grade"]
    evaluation.rule_version = payload["rule_version"]
    evaluation.evaluated_at = payload["evaluated_at"]


def _serialize_evaluation(evaluation: MatchEvaluation, match: Match) -> dict[str, Any]:
    return {
        "id": evaluation.id,
        "match_id": evaluation.match_id,
        "prediction_version_id": evaluation.prediction_version_id,
        "evaluation_status": evaluation.evaluation_status,
        "actual_home_score": evaluation.actual_home_score,
        "actual_away_score": evaluation.actual_away_score,
        "outcome_hit": evaluation.outcome_hit,
        "exact_score_hit": evaluation.exact_score_hit,
        "home_goals_hit": evaluation.home_goals_hit,
        "away_goals_hit": evaluation.away_goals_hit,
        "total_goals_hit": evaluation.total_goals_hit,
        "grade": evaluation.grade,
        "rule_version": evaluation.rule_version,
        "evaluated_at": evaluation.evaluated_at,
        "stage": match.stage,
        "status": match.status,
        "score": match.score,
    }
