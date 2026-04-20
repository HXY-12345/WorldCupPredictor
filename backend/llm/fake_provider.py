"""核心功能：提供不依赖外部模型的确定性预测 provider 测试桩。"""

from datetime import UTC, datetime
from typing import Any

from backend.llm.provider import PredictionProvider, PredictionRequest


class FakePredictionProvider(PredictionProvider):
    """基于输入上下文生成确定性预测结果的测试 provider。"""

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        match_facts = _extract_match_facts(request)
        seed = _resolve_seed(match_facts)
        home_goals = 1 + (seed % 2)
        away_goals = seed % 2

        return {
            "predicted_score": {"home": home_goals, "away": away_goals},
            "outcome_pick": _derive_outcome(home_goals, away_goals),
            "home_goals_pick": home_goals,
            "away_goals_pick": away_goals,
            "total_goals_pick": home_goals + away_goals,
            "confidence": 68,
            "reasoning_summary": _build_reasoning_summary(match_facts),
            "evidence_items": _build_evidence_items(match_facts),
            "uncertainties": _build_uncertainties(match_facts),
            "model_meta": {
                "provider": "fake",
                "model_name": "fake-prediction-v1",
                "predicted_at": datetime.now(UTC).isoformat(),
            },
            "input_snapshot": match_facts,
        }


def _extract_match_facts(request: PredictionRequest) -> dict[str, Any]:
    if request.metadata and isinstance(request.metadata.get("match_facts"), dict):
        return request.metadata["match_facts"]

    for message in reversed(request.messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if not isinstance(content, str):
            continue
        try:
            import json

            payload = json.loads(content)
        except Exception:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("match_facts"), dict):
            return payload["match_facts"]

    raise ValueError("Prediction request did not include match facts.")


def _resolve_seed(match_facts: dict[str, Any]) -> int:
    if isinstance(match_facts.get("official_match_number"), int):
        return int(match_facts["official_match_number"])

    match_id = str(match_facts.get("match_id") or "")
    digits = "".join(character for character in match_id if character.isdigit())
    return int(digits or "1")


def _build_reasoning_summary(match_facts: dict[str, Any]) -> str:
    home_team = (match_facts.get("home_team") or {}).get("name") or "主队"
    away_team = (match_facts.get("away_team") or {}).get("name") or "客队"
    venue = match_facts.get("venue") or "比赛场地"
    return f"结合已提供的赛程事实，{home_team}在{venue}更被看好，预计会小胜{away_team}。"


def _build_evidence_items(match_facts: dict[str, Any]) -> list[dict[str, Any]]:
    match_id = match_facts.get("match_id") or "未知比赛"
    stage = match_facts.get("stage") or "未知阶段"
    venue = match_facts.get("venue") or "待定场地"
    kickoff = match_facts.get("kickoff_label") or match_facts.get("time") or "待定"

    return [
        {
            "claim": f"比赛 {match_id} 当前仍是赛前状态，适合进行赛前预测。",
            "source_name": "官方赛程",
            "source_url": "https://www.fifa.com",
            "source_level": 1,
        },
        {
            "claim": f"比赛场地为 {venue}，主客队都需要围绕这一场地条件准备。",
            "source_name": "比赛场地",
            "source_url": "https://www.fifa.com",
            "source_level": 1,
        },
        {
            "claim": f"本场属于 {stage}，当前开球标识为 {kickoff}，可直接依据赛程事实生成预测。",
            "source_name": "赛事阶段",
            "source_url": "https://www.fifa.com",
            "source_level": 1,
        },
    ]


def _build_uncertainties(match_facts: dict[str, Any]) -> list[str]:
    uncertainties: list[str] = []
    if match_facts.get("status") != "not_started":
        uncertainties.append("比赛状态可能在最近一次刷新后发生变化。")
    if not match_facts.get("home_team") or not match_facts.get("away_team"):
        uncertainties.append("球队信息仍不完整。")
    return uncertainties or ["双方首发与临场状态仍存在不确定性。"]


def _derive_outcome(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home_win"
    if home_goals < away_goals:
        return "away_win"
    return "draw"
