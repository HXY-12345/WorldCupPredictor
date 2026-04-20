"""核心功能：验证 fake prediction provider 能产出合法结构化预测结果。"""

from backend.llm.fake_provider import FakePredictionProvider
from backend.services.prediction_context import PredictionContext
from backend.services.prediction_prompt import build_prediction_request
from backend.services.prediction_schema import parse_prediction_output


def _context() -> PredictionContext:
    return PredictionContext(
        match_facts={
            "match_id": "fwc2026-m001",
            "official_match_number": 1,
            "date": "2026-06-11",
            "time": "18:00",
            "stage": "Group Stage",
            "group_name": "A",
            "venue": "Mexico City Stadium",
            "home_team": {"name": "Mexico"},
            "away_team": {"name": "South Africa"},
        },
        database_context={
            "prediction_count": 0,
            "latest_prediction_summary": None,
            "recent_prediction_summaries": [],
        },
    )


def test_fake_prediction_provider_generates_valid_structured_output():
    request = build_prediction_request(_context())
    provider = FakePredictionProvider()

    result = parse_prediction_output(provider.predict(request))

    assert result.model_meta.provider == "fake"
    assert result.model_meta.model_name == "fake-prediction-v1"
    assert len(result.evidence_items) == 3
    assert result.predicted_score.home == 2
    assert result.predicted_score.away == 1
    assert result.outcome_pick == "home_win"
