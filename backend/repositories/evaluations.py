"""核心功能：查询赛后评估记录并按总览与阶段聚合统计结果。"""

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.match import Match
from backend.models.match_evaluation import MatchEvaluation


class MatchEvaluationRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_payload(self) -> dict[str, Any]:
        items = [self._serialize(evaluation, match) for evaluation, match in self._list_rows()]
        return {
            "items": items,
            "total": len(items),
        }

    def get_detail_payload(self, match_id: str) -> dict[str, Any] | None:
        row = self.session.execute(
            select(MatchEvaluation, Match)
            .join(Match, Match.id == MatchEvaluation.match_id)
            .where(MatchEvaluation.match_id == match_id)
        ).first()
        if row is None:
            return None

        evaluation, match = row
        return self._serialize(evaluation, match)

    def summary_payload(self) -> dict[str, Any]:
        rows = self._list_rows()
        return _build_analytics_payload(rows)

    def by_stage_payload(self) -> dict[str, Any]:
        rows = self._list_rows()
        grouped_rows: dict[str, list[tuple[MatchEvaluation, Match]]] = defaultdict(list)
        stage_sort_keys: dict[str, tuple[int, str]] = {}

        for evaluation, match in rows:
            stage = match.stage or "Unknown"
            grouped_rows[stage].append((evaluation, match))
            sort_order = match.sort_order if match.sort_order is not None else 10**9
            stage_sort_keys[stage] = min(stage_sort_keys.get(stage, (sort_order, stage)), (sort_order, stage))

        ordered_stages = sorted(grouped_rows, key=lambda stage: stage_sort_keys[stage])
        items = []
        for stage in ordered_stages:
            payload = _build_analytics_payload(grouped_rows[stage])
            items.append({"stage": stage, **payload})

        return {
            "items": items,
            "total": len(items),
        }

    def _list_rows(self) -> list[tuple[MatchEvaluation, Match]]:
        statement = (
            select(MatchEvaluation, Match)
            .join(Match, Match.id == MatchEvaluation.match_id)
            .order_by(Match.date.asc(), Match.sort_order.asc(), Match.id.asc())
        )
        return list(self.session.execute(statement).all())

    def _serialize(self, evaluation: MatchEvaluation, match: Match) -> dict[str, Any]:
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


def _build_analytics_payload(rows: list[tuple[MatchEvaluation, Match]]) -> dict[str, Any]:
    scored_rows = [evaluation for evaluation, _ in rows if evaluation.evaluation_status == "scored"]
    total_scored_matches = len(scored_rows)

    return {
        "total_scored_matches": total_scored_matches,
        "no_prediction_matches": sum(
            1 for evaluation, _ in rows if evaluation.evaluation_status == "no_prediction"
        ),
        "pending_result_matches": sum(
            1 for evaluation, _ in rows if evaluation.evaluation_status == "pending_result"
        ),
        "invalid_matches": sum(1 for evaluation, _ in rows if evaluation.evaluation_status == "invalid"),
        "dimensions": {
            "outcome": _dimension_payload(scored_rows, "outcome_hit"),
            "exact_score": _dimension_payload(scored_rows, "exact_score_hit"),
            "home_goals": _dimension_payload(scored_rows, "home_goals_hit"),
            "away_goals": _dimension_payload(scored_rows, "away_goals_hit"),
            "total_goals": _dimension_payload(scored_rows, "total_goals_hit"),
        },
        "grade_distribution": {
            "core_hit": sum(1 for evaluation in scored_rows if evaluation.grade == "core_hit"),
            "partial_hit": sum(1 for evaluation in scored_rows if evaluation.grade == "partial_hit"),
            "miss": sum(1 for evaluation in scored_rows if evaluation.grade == "miss"),
        },
    }


def _dimension_payload(scored_rows: list[MatchEvaluation], field_name: str) -> dict[str, Any]:
    hit_count = sum(1 for evaluation in scored_rows if getattr(evaluation, field_name) is True)
    total = len(scored_rows)
    return {
        "hit": hit_count,
        "rate": round(hit_count / total, 4) if total else 0.0,
    }
