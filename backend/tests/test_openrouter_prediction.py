"""核心功能：验证 OpenRouter 预测 provider 的请求转发、响应解析和限流错误映射。"""

import json

import httpx
import pytest

from backend.llm.openrouter import OpenRouterSettings
from backend.llm.openrouter_prediction import OpenRouterPredictionProvider
from backend.llm.provider import PredictionProviderResponseError
from backend.services.prediction_context import PredictionContext
from backend.services.prediction_prompt import build_prediction_request
from backend.services.prediction_schema import parse_prediction_output


def _context() -> PredictionContext:
    return PredictionContext(
        match_facts={
            "match_id": "fwc2026-m001",
            "official_match_number": 1,
            "kickoff_label": "M001",
            "sort_order": 1,
            "date": "2026-06-11",
            "time": "18:00",
            "stage": "Group Stage",
            "group_name": "A",
            "venue": "Mexico City Stadium",
            "home_team": {"name": "Mexico"},
            "away_team": {"name": "South Africa"},
            "status": "not_started",
            "score": None,
            "prediction": None,
        },
        database_context={
            "prediction_count": 0,
            "latest_prediction_summary": None,
            "recent_prediction_summaries": [],
        },
    )


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(
        base_url="https://openrouter.ai/api/v1/chat/completions",
        model="qwen/qwen3.5-flash-20260224",
        api_key="sk-or-v1-test-key",
    )


class DummyOpenRouterClient:
    def __init__(self, payload: dict | None = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.calls: list[dict] = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.payload


def _prediction_payload() -> dict:
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
        "input_snapshot": _context().match_facts,
    }


def test_openrouter_prediction_provider_parses_completion_and_forwards_request_settings():
    request = build_prediction_request(_context())
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(_prediction_payload(), ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)
    parsed = parse_prediction_output(result)

    assert client.calls[0]["messages"] == request.messages
    assert client.calls[0]["response_format"] == request.response_format
    assert client.calls[0]["plugins"] == request.plugins
    assert client.calls[0]["provider"] == request.provider
    assert parsed.predicted_score.home == 2
    assert parsed.model_meta.provider == "openrouter"


def test_openrouter_prediction_provider_maps_429_to_response_error():
    request = build_prediction_request(_context())
    response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", _settings().base_url),
        text="Too Many Requests",
    )
    client = DummyOpenRouterClient(
        error=httpx.HTTPStatusError("429 Too Many Requests", request=response.request, response=response)
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    with pytest.raises(PredictionProviderResponseError) as exc_info:
        provider.predict(request)

    assert "429" in str(exc_info.value)


def test_openrouter_prediction_provider_maps_invalid_json_to_response_error():
    request = build_prediction_request(_context())
    client = DummyOpenRouterClient(
        error=json.JSONDecodeError("Expecting value", "", 0)
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    with pytest.raises(PredictionProviderResponseError) as exc_info:
        provider.predict(request)

    assert "JSON" in str(exc_info.value)


def test_openrouter_prediction_provider_strips_think_prefix_before_loading_json():
    request = build_prediction_request(_context())
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": "</think>\n\n" + json.dumps(_prediction_payload(), ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)

    assert result["predicted_score"]["home"] == 2
    assert result["model_meta"]["provider"] == "openrouter"


def test_openrouter_prediction_provider_backfills_partial_input_snapshot_from_request_metadata():
    request = build_prediction_request(_context())
    payload = _prediction_payload()
    payload["input_snapshot"] = {"match_id": "fwc2026-m001"}
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)

    assert result["input_snapshot"]["match_id"] == "fwc2026-m001"
    assert result["input_snapshot"]["date"] == "2026-06-11"
    assert result["input_snapshot"]["home_team"]["name"] == "Mexico"


def test_openrouter_prediction_provider_prefers_real_model_name_over_generic_version_field():
    request = build_prediction_request(_context())
    payload = _prediction_payload()
    payload["model_meta"] = {
        "provider": "openrouter",
        "version": "1.0",
        "timestamp": "2026-04-19T12:00:00Z",
    }
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)

    assert result["model_meta"]["model_name"] == "qwen/qwen3.5-flash-20260224"


def test_openrouter_prediction_provider_overrides_bogus_model_name_with_actual_payload_model():
    request = build_prediction_request(_context())
    payload = _prediction_payload()
    payload["model_meta"] = {
        "provider": "openrouter",
        "model_name": "1.0",
        "predicted_at": "2026-04-19T12:00:00Z",
    }
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)

    assert result["model_meta"]["model_name"] == "qwen/qwen3.5-flash-20260224"


def test_openrouter_prediction_provider_normalizes_percentage_confidence_strings():
    request = build_prediction_request(_context())
    payload = _prediction_payload()
    payload["confidence"] = "55%"
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)
    parsed = parse_prediction_output(result)

    assert parsed.confidence == 55


def test_openrouter_prediction_provider_normalizes_text_confidence_and_string_team_snapshots():
    request = build_prediction_request(_context())
    payload = _prediction_payload()
    payload["confidence"] = "低"
    payload["input_snapshot"] = {
        "match_id": "fwc2026-m001",
        "date": "2026-06-11",
        "time": "18:00",
        "stage": "Group Stage",
        "group_name": "A",
        "venue": "Mexico City Stadium",
        "home_team": "Mexico",
        "away_team": "South Africa",
    }
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload, ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(_settings(), client=client)

    result = provider.predict(request)
    parsed = parse_prediction_output(result)

    assert parsed.confidence == 35
    assert parsed.input_snapshot.home_team == {"name": "Mexico"}
    assert parsed.input_snapshot.away_team == {"name": "South Africa"}
