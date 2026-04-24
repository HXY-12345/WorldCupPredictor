"""核心功能：验证预测 prompt 与请求载体的生成规则。"""

from backend.services.prediction_context import PredictionContext
from backend.services.prediction_prompt import (
    build_prediction_messages,
    build_prediction_request,
    build_prediction_system_prompt,
    build_prediction_user_prompt,
)


def _context() -> PredictionContext:
    return PredictionContext(
        match_facts={
            "match_id": "fwc2026-m001",
            "date": "2026-06-11",
            "time": "18:00",
            "stage": "Group Stage",
            "group_name": "A",
            "venue": "Mexico City Stadium",
            "home_team": {"name": "Mexico"},
            "away_team": {"name": "South Africa"},
        },
        database_context={},
    )


def test_build_prediction_system_prompt_requires_fact_only_chinese_output():
    prompt = build_prediction_system_prompt()

    assert "Return exactly one compact JSON object" in prompt
    assert "supplied JSON facts" in prompt
    assert "Do not browse" in prompt
    assert "recent prediction history" not in prompt
    assert "Chinese" in prompt


def test_build_prediction_system_prompt_forbids_echoing_request_wrapper_into_input_snapshot():
    prompt = build_prediction_system_prompt()

    assert "input_snapshot must contain only the match_facts object" in prompt
    assert "Do not copy the outer request payload" in prompt
    assert "Keep reasoning_summary concise" in prompt


def test_build_prediction_user_prompt_includes_match_facts_without_history():
    prompt = build_prediction_user_prompt(_context())

    assert '"match_id": "fwc2026-m001"' in prompt
    assert "Mexico City Stadium" in prompt
    assert '"database_context"' not in prompt


def test_build_prediction_request_wraps_messages_and_response_format():
    request = build_prediction_request(_context())

    assert len(request.messages) == 2
    assert request.messages[0]["role"] == "system"
    assert request.response_format["json_schema"]["name"] == "worldcup_prediction_output"
    assert request.metadata["match_id"] == "fwc2026-m001"


def test_build_prediction_request_can_disable_response_format():
    request = build_prediction_request(_context(), use_response_format=False)

    assert request.response_format is None
