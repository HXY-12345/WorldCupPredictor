"""核心功能：验证预测输出结构化 schema 的校验、规范化和 JSON Schema 导出。"""

import json

import pytest

from backend.services.prediction_schema import (
    PredictionSchemaError,
    parse_prediction_output,
    prediction_output_json_schema,
    prediction_output_response_format,
)


def _valid_prediction_payload() -> dict:
    return {
        "predicted_score": {"home": 2, "away": 1},
        "outcome_pick": "home_win",
        "home_goals_pick": 2,
        "away_goals_pick": 1,
        "total_goals_pick": 3,
        "confidence": 78,
        "reasoning_summary": "Mexico looks stronger at home and has better recent form.",
        "evidence_items": [
            {
                "claim": "FIFA ranking gap favors Mexico.",
                "source_name": "fifa_ranking",
                "source_url": "https://www.fifa.com",
                "source_level": 2,
            },
            {
                "claim": "South Africa has mixed recent form.",
                "source_name": "recent_form",
                "source_url": "https://example.com/form",
                "source_level": 2,
            },
            {
                "claim": "Mexico City venue supports the home side.",
                "source_name": "venue_report",
                "source_url": "https://example.com/venue",
                "source_level": 3,
            },
        ],
        "uncertainties": ["Starting lineups are not fully confirmed."],
        "model_meta": {
            "provider": "openrouter",
            "model_name": "qwen/qwen3.5-flash-20260224",
            "predicted_at": "2026-04-19T12:00:00Z",
        },
        "input_snapshot": {
            "match_id": "fwc2026-m001",
            "date": "2026-06-11",
            "time": "18:00",
            "stage": "Group Stage",
            "group_name": "A",
            "venue": "Mexico City Stadium",
            "home_team": {"name": "Mexico", "flag": "MX"},
            "away_team": {"name": "South Africa", "flag": "ZA"},
        },
    }


def test_prediction_output_schema_exposes_required_fields():
    schema = prediction_output_json_schema()

    assert schema["type"] == "object"
    assert "predicted_score" in schema["properties"]
    assert "evidence_items" in schema["properties"]
    assert "model_meta" in schema["required"]
    assert "input_snapshot" in schema["required"]


def test_prediction_output_response_format_wraps_json_schema():
    response_format = prediction_output_response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["type"] == "object"


def test_parse_prediction_output_accepts_json_string_payload():
    result = parse_prediction_output(json.dumps(_valid_prediction_payload(), ensure_ascii=False))

    assert result.predicted_score.home == 2
    assert result.outcome_pick == "home_win"
    assert result.evidence_items[0].source_level == 2
    assert result.model_meta.model_name == "qwen/qwen3.5-flash-20260224"


def test_parse_prediction_output_rejects_invalid_json():
    with pytest.raises(PredictionSchemaError):
        parse_prediction_output("{not-json}")


def test_parse_prediction_output_rejects_inconsistent_outcome():
    payload = _valid_prediction_payload()
    payload["outcome_pick"] = "draw"

    with pytest.raises(PredictionSchemaError):
        parse_prediction_output(payload)


def test_parse_prediction_output_rejects_too_few_evidence_items():
    payload = _valid_prediction_payload()
    payload["evidence_items"] = payload["evidence_items"][:2]

    with pytest.raises(PredictionSchemaError):
        parse_prediction_output(payload)


def test_parse_prediction_output_normalizes_prefixed_relaxed_json_output():
    raw_output = """
</think>

{
  "predicted_score": "1-2",
  "outcome_pick": "Away Win",
  "home_goals_pick": 1,
  "away_goals_pick": 2,
  "total_goals_pick": 3,
  "confidence": 55,
  "reasoning_summary": "Prediction aligns with provided probability data.",
  "evidence_items": [
    "Venue is Mexico City Stadium, favoring home team Mexico.",
    "Both teams have empty form arrays, indicating no recent performance data.",
    "Provided prediction probabilities show 44% chance for away win."
  ],
  "uncertainties": "FIFA ranks are null for both teams.",
  "model_meta": {
    "provider": "openrouter",
    "model_name": "qwen/qwen3.5-flash-20260224",
    "predicted_at": "2026-04-19T12:00:00Z",
    "version": "1.0",
    "timestamp": "2026-04-18T00:00:00Z"
  },
  "input_snapshot": {
    "match_facts": {
      "match_id": "fwc2026-m001",
      "date": "2026-06-11",
      "time": "待定",
      "stage": "小组赛",
      "group_name": "A",
      "venue": "Mexico City Stadium",
      "home_team": {"name": "Mexico", "flag": "🇲🇽"},
      "away_team": {"name": "South Africa", "flag": "🇿🇦"}
    },
    "database_context": {"prediction_count": 0}
  }
}
""".strip()

    result = parse_prediction_output(raw_output)

    assert result.predicted_score.home == 1
    assert result.predicted_score.away == 2
    assert result.outcome_pick == "away_win"
    assert len(result.evidence_items) == 3
    assert result.evidence_items[0].source_name == "provided_input"
    assert result.uncertainties == ["FIFA ranks are null for both teams."]
    assert result.input_snapshot.match_id == "fwc2026-m001"


def test_parse_prediction_output_normalizes_text_confidence_and_string_team_snapshots():
    payload = _valid_prediction_payload()
    payload["confidence"] = "低"
    payload["input_snapshot"]["home_team"] = "Korea Republic"
    payload["input_snapshot"]["away_team"] = "Czechia"

    result = parse_prediction_output(payload)

    assert result.confidence == 35
    assert result.input_snapshot.home_team == {"name": "Korea Republic"}
    assert result.input_snapshot.away_team == {"name": "Czechia"}
