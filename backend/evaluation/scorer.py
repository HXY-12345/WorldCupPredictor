"""核心功能：按常规时间比分计算预测命中维度与分层评分。"""

from typing import Any

RULE_VERSION = "v1"


def score_prediction(
    prediction_payload: dict[str, Any],
    *,
    actual_home_score: int,
    actual_away_score: int,
) -> dict[str, Any]:
    predicted_home, predicted_away = _extract_predicted_score(prediction_payload)
    predicted_outcome = prediction_payload.get("outcome_pick") or _derive_outcome(predicted_home, predicted_away)
    actual_outcome = _derive_outcome(actual_home_score, actual_away_score)

    exact_score_hit = predicted_home == actual_home_score and predicted_away == actual_away_score
    outcome_hit = predicted_outcome == actual_outcome
    home_goals_hit = predicted_home == actual_home_score
    away_goals_hit = predicted_away == actual_away_score
    total_goals_hit = (predicted_home + predicted_away) == (actual_home_score + actual_away_score)

    if exact_score_hit or (outcome_hit and (home_goals_hit or away_goals_hit or total_goals_hit)):
        grade = "core_hit"
    elif any((outcome_hit, exact_score_hit, home_goals_hit, away_goals_hit, total_goals_hit)):
        grade = "partial_hit"
    else:
        grade = "miss"

    return {
        "outcome_hit": outcome_hit,
        "exact_score_hit": exact_score_hit,
        "home_goals_hit": home_goals_hit,
        "away_goals_hit": away_goals_hit,
        "total_goals_hit": total_goals_hit,
        "grade": grade,
    }


def _extract_predicted_score(prediction_payload: dict[str, Any]) -> tuple[int, int]:
    predicted_score = prediction_payload.get("predicted_score")
    if isinstance(predicted_score, dict):
        home = predicted_score.get("home")
        away = predicted_score.get("away")
    else:
        home = prediction_payload.get("home_goals_pick")
        away = prediction_payload.get("away_goals_pick")

    if not isinstance(home, int) or not isinstance(away, int):
        raise ValueError("Prediction payload must contain integer home and away goals.")

    return home, away


def _derive_outcome(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home_win"
    if home_goals < away_goals:
        return "away_win"
    return "draw"
