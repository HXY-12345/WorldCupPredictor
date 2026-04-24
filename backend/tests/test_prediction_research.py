"""核心功能：验证 fake 与 OpenRouter Research 阶段的结构化输出、工具循环与容错行为。"""

import json
from pathlib import Path
import time
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterSettings
from backend.llm.provider import PredictionProviderResponseError, PredictionProviderTimeoutError
from backend.main import create_app
from backend.services.prediction_research import (
    OpenRouterPredictionResearcher,
    build_default_prediction_researcher,
    run_prediction_research,
    run_fake_prediction_research,
)


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "id": "fwc2026-m001",
                        "official_match_number": 1,
                        "kickoff_label": "M001",
                        "sort_order": 1,
                        "date": "2026-06-11",
                        "time": "18:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": 12, "form": ["W", "D"]},
                        "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": 47, "form": ["L", "W"]},
                        "status": "not_started",
                        "score": None,
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-03-31T00:00:00Z",
                "total": 1,
            }
        ),
        encoding="utf-8",
    )


def _research_settings() -> OpenRouterSettings:
    return OpenRouterSettings(
        base_url="https://openrouter.ai/api/v1/chat/completions",
        model="qwen/qwen3.5-flash-02-23",
        api_key="sk-or-v1-test-key",
        enable_web_plugin=False,
        enable_response_healing=True,
        require_parameters=True,
    )


class DummyOpenRouterClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return self.payload


class SequencedOpenRouterClient:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = list(payloads)
        self.calls: list[dict] = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return self.payloads.pop(0)


class SlowOpenRouterClient:
    def create_chat_completion(self, **kwargs):
        time.sleep(0.2)
        return {"choices": []}


class ExplodingResearchExecutor:
    def run(self, session_factory, match_id):
        raise PredictionProviderResponseError("Research stage failed upstream.")


class DummyDuckDuckGoSearchTool:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search(self, query: str, *, max_results: int) -> dict:
        self.calls.append(
            {
                "query": query,
                "max_results": max_results,
            }
        )
        return {
            "results": [
                {
                    "title": "Mexico vs South Africa preview",
                    "url": "https://example.com/preview",
                    "domain": "example.com",
                    "snippet": "Mexico enters with steadier recent form and venue familiarity.",
                },
                {
                    "title": "Mexico squad update",
                    "url": "https://example.com/mexico-squad",
                    "domain": "example.com",
                    "snippet": "Mexico are expected to keep a stable squad core.",
                },
            ]
        }


def test_run_fake_prediction_research_returns_stable_contract():
    runtime_dir = _runtime_dir("prediction_research")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        research = run_fake_prediction_research(app.state.session_factory, "fwc2026-m001")

    assert research.planner_model == "fake-research-v1"
    assert research.used_fallback_sources is False
    assert research.search_plan["match_id"] == "fwc2026-m001"
    assert research.search_plan["queries"][0]["query"].startswith("Mexico vs South Africa")
    assert len(research.search_plan["queries"]) >= 4
    assert {query["topic"] for query in research.search_plan["queries"]} >= {
        "match_preview",
        "home_team_form",
        "away_team_form",
        "venue_context",
    }
    assert research.search_trace["completed"] is True
    assert research.search_trace["generated_from_match_facts"] is True
    assert research.search_trace["fallback_mode"] == "local_match_fact_synthesis"
    assert len(research.search_documents) >= 4
    assert research.search_documents[0]["source_tier"] == "controlled"
    assert "Mexico City Stadium" in research.search_documents[0]["content_text"]
    assert any("FIFA rank" in document["content_text"] for document in research.search_documents)
    assert any("Group Stage" in document["content_text"] for document in research.search_documents)


def test_run_prediction_research_preserves_fallback_reason_and_uses_richer_local_bundle():
    runtime_dir = _runtime_dir("prediction_research_fallback")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_fallback.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        research = run_prediction_research(
            app.state.session_factory,
            "fwc2026-m001",
            researcher=ExplodingResearchExecutor(),
        )

    assert research.planner_model == "fallback-research-v1"
    assert research.used_fallback_sources is True
    assert research.search_trace["fallback_reason"] == "Research stage failed upstream."
    assert research.search_trace["generated_from_match_facts"] is True
    assert research.search_trace["fallback_mode"] == "local_match_fact_synthesis"
    assert len(research.search_plan["queries"]) >= 4
    assert len(research.search_documents) >= 4


def test_openrouter_prediction_researcher_parses_structured_payload_and_forwards_request_settings():
    runtime_dir = _runtime_dir("prediction_research_openrouter")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_openrouter.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "search_plan": {
                                    "match_id": "fwc2026-m001",
                                    "queries": [
                                        {"topic": "preview", "query": "Mexico vs South Africa preview"},
                                    ],
                                    "source_policy": "controlled-first",
                                },
                                "search_trace": {
                                    "completed": True,
                                    "executed_queries": [
                                        {"topic": "preview", "query": "Mexico vs South Africa preview"},
                                    ],
                                    "opened_urls": ["https://example.com/preview"],
                                    "round_count": 1,
                                },
                                "search_documents": [
                                    {
                                        "query": "Mexico vs South Africa preview",
                                        "title": "Mexico vs South Africa preview",
                                        "url": "https://example.com/preview",
                                        "domain": "example.com",
                                        "source_tier": "controlled",
                                        "published_at": "2026-04-21T08:00:00Z",
                                        "fetched_at": "2026-04-22T01:00:00Z",
                                        "content_text": "Mexico enters with steadier recent form and venue familiarity.",
                                        "content_hash": "hash-preview",
                                    }
                                ],
                                "used_fallback_sources": False,
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        researcher = OpenRouterPredictionResearcher(_research_settings(), client=client)
        research = researcher.run(app.state.session_factory, "fwc2026-m001")

    assert research.planner_model == "qwen/qwen3.5-flash-02-23"
    assert research.search_plan["match_id"] == "fwc2026-m001"
    assert research.search_trace["completed"] is True
    assert research.search_documents[0]["domain"] == "example.com"
    assert client.calls[0]["plugins"] == [{"id": "response-healing"}]
    assert client.calls[0]["provider"] == {"require_parameters": True}
    assert "Mexico" in client.calls[0]["messages"][1]["content"]


def test_openrouter_prediction_researcher_runs_duckduckgo_tool_loop_and_records_trace():
    runtime_dir = _runtime_dir("prediction_research_tool_loop")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_tool_loop.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)
    client = SequencedOpenRouterClient(
        payloads=[
            {
                "model": "qwen/qwen3.5-flash-02-23",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "toolcall_1",
                                    "type": "function",
                                    "function": {
                                        "name": "duckduckgo_search",
                                        "arguments": json.dumps(
                                            {
                                                "query": "Mexico vs South Africa preview",
                                                "max_results": 3,
                                            },
                                            ensure_ascii=False,
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            },
            {
                "model": "qwen/qwen3.5-flash-02-23",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "search_plan": {
                                        "match_id": "fwc2026-m001",
                                        "queries": [
                                            {
                                                "topic": "preview",
                                                "query": "Mexico vs South Africa preview",
                                            }
                                        ],
                                        "source_policy": "duckduckgo-tool-first",
                                    },
                                    "search_trace": {
                                        "completed": True,
                                        "executed_queries": [],
                                        "opened_urls": [],
                                        "round_count": 0,
                                    },
                                    "search_documents": [],
                                    "used_fallback_sources": False,
                                },
                                ensure_ascii=False,
                            ),
                        }
                    }
                ],
            },
        ]
    )
    search_tool = DummyDuckDuckGoSearchTool()

    with TestClient(app):
        researcher = OpenRouterPredictionResearcher(
            _research_settings(),
            client=client,
            search_tool=search_tool,
            max_tool_rounds=2,
        )
        research = researcher.run(app.state.session_factory, "fwc2026-m001")

    assert search_tool.calls == [
        {
            "query": "Mexico vs South Africa preview",
            "max_results": 3,
        }
    ]
    assert client.calls[0]["tools"][0]["function"]["name"] == "duckduckgo_search"
    assert client.calls[0]["tool_choice"] == "auto"
    assert "parallel_tool_calls" not in client.calls[0]
    assert research.planner_model == "qwen/qwen3.5-flash-02-23"
    assert research.search_plan["source_policy"] == "duckduckgo-tool-first"
    assert research.search_trace["tool_name"] == "duckduckgo_search"
    assert research.search_trace["round_count"] == 1
    assert research.search_trace["generated_from_match_facts"] is False
    assert research.search_trace["executed_queries"] == [
        {
            "query": "Mexico vs South Africa preview",
            "max_results": 3,
            "result_count": 2,
        }
    ]
    assert research.search_trace["opened_urls"] == [
        "https://example.com/preview",
        "https://example.com/mexico-squad",
    ]
    assert len(research.search_documents) == 2
    assert research.search_documents[0]["source_tier"] == "search"
    assert research.search_documents[0]["query"] == "Mexico vs South Africa preview"
    assert research.search_documents[0]["domain"] == "example.com"
    assert research.used_fallback_sources is False


def test_run_prediction_research_falls_back_when_tool_loop_exceeds_max_rounds():
    runtime_dir = _runtime_dir("prediction_research_tool_loop_rounds")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_tool_loop_rounds.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)
    client = SequencedOpenRouterClient(
        payloads=[
            {
                "model": "qwen/qwen3.5-flash-02-23",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "toolcall_1",
                                    "type": "function",
                                    "function": {
                                        "name": "duckduckgo_search",
                                        "arguments": json.dumps(
                                            {
                                                "query": "Mexico vs South Africa preview",
                                                "max_results": 3,
                                            },
                                            ensure_ascii=False,
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            },
            {
                "model": "qwen/qwen3.5-flash-02-23",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "toolcall_2",
                                    "type": "function",
                                    "function": {
                                        "name": "duckduckgo_search",
                                        "arguments": json.dumps(
                                            {
                                                "query": "South Africa team news",
                                                "max_results": 3,
                                            },
                                            ensure_ascii=False,
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ],
            },
        ]
    )
    search_tool = DummyDuckDuckGoSearchTool()

    with TestClient(app):
        research = run_prediction_research(
            app.state.session_factory,
            "fwc2026-m001",
            researcher=OpenRouterPredictionResearcher(
                _research_settings(),
                client=client,
                search_tool=search_tool,
                max_tool_rounds=1,
            ),
        )

    assert research.planner_model == "fallback-research-v1"
    assert research.used_fallback_sources is True
    assert "round" in research.search_trace["fallback_reason"].lower()
    assert research.search_trace["generated_from_match_facts"] is True


def test_openrouter_prediction_researcher_tolerates_non_object_nested_sections():
    runtime_dir = _runtime_dir("prediction_research_openrouter_fuzzy")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_openrouter_fuzzy.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "search_plan": ["unexpected-shape"],
                                "search_trace": "unexpected-shape",
                                "search_documents": [
                                    {
                                        "title": "Mexico vs South Africa preview",
                                        "url": "https://example.com/preview",
                                        "content_text": "Mexico enters with steadier recent form.",
                                    },
                                    "drop-me",
                                ],
                                "used_fallback_sources": "true",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        researcher = OpenRouterPredictionResearcher(_research_settings(), client=client)
        research = researcher.run(app.state.session_factory, "fwc2026-m001")

    assert research.search_plan == {
        "match_id": "fwc2026-m001",
        "queries": [],
        "source_policy": "controlled-first",
    }
    assert research.search_trace == {
        "completed": False,
        "executed_queries": [],
        "opened_urls": [],
        "round_count": 0,
    }
    assert research.used_fallback_sources is True
    assert len(research.search_documents) == 1
    assert research.search_documents[0]["domain"] == "example.com"
    assert research.search_documents[0]["query"] == ""


def test_openrouter_prediction_researcher_extracts_json_from_wrapped_text():
    runtime_dir = _runtime_dir("prediction_research_openrouter_wrapped")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_openrouter_wrapped.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)
    wrapped_payload = {
        "search_plan": {
            "match_id": "fwc2026-m001",
            "queries": [{"topic": "preview", "query": "Mexico vs South Africa preview"}],
            "source_policy": "controlled-first",
        },
        "search_trace": {
            "completed": True,
            "executed_queries": [{"topic": "preview", "query": "Mexico vs South Africa preview"}],
            "opened_urls": ["https://example.com/preview"],
            "round_count": 1,
        },
        "search_documents": [
            {
                "query": "Mexico vs South Africa preview",
                "title": "Mexico vs South Africa preview",
                "url": "https://example.com/preview",
                "domain": "example.com",
                "source_tier": "controlled",
                "published_at": None,
                "fetched_at": "2026-04-22T01:00:00Z",
                "content_text": "Mexico enters with steadier recent form and venue familiarity.",
                "content_hash": "hash-preview",
            }
        ],
        "used_fallback_sources": False,
    }
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": "</think>\n```json\n"
                        + json.dumps(wrapped_payload, ensure_ascii=False)
                        + "\n```",
                    }
                }
            ],
        }
    )

    with TestClient(app):
        researcher = OpenRouterPredictionResearcher(_research_settings(), client=client)
        research = researcher.run(app.state.session_factory, "fwc2026-m001")

    assert research.search_trace["completed"] is True
    assert research.search_documents[0]["title"] == "Mexico vs South Africa preview"


def test_openrouter_prediction_researcher_raises_timeout_when_client_hangs():
    runtime_dir = _runtime_dir("prediction_research_openrouter_timeout")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_research_openrouter_timeout.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        researcher = OpenRouterPredictionResearcher(
            _research_settings(),
            client=SlowOpenRouterClient(),
            timeout_seconds=0.01,
        )
        started_at = time.perf_counter()
        with pytest.raises(PredictionProviderTimeoutError):
            researcher.run(app.state.session_factory, "fwc2026-m001")
        elapsed = time.perf_counter() - started_at

    assert elapsed < 0.1


def test_build_default_prediction_researcher_uses_configured_duckduckgo_backend_chain():
    runtime_dir = _runtime_dir("prediction_research_builder")
    model_config_path = runtime_dir / "openrouter.research.model.json"
    key_path = runtime_dir / "openrouter.key"
    model_config_path.write_text(
        json.dumps(
            {
                "base_url": "https://openrouter.ai/api/v1/chat/completions",
                "model": "qwen/qwen3.6-plus",
                "temperature": 0.1,
                "max_tokens": 1400,
                "enable_web_plugin": False,
                "enable_response_healing": False,
                "require_parameters": True,
            }
        ),
        encoding="utf-8",
    )
    key_path.write_text("sk-or-v1-test-key", encoding="utf-8")

    settings = Settings(
        prediction_research_openrouter_model_config_path=str(model_config_path),
        prediction_research_openrouter_key_path=str(key_path),
        prediction_research_duckduckgo_enabled=True,
        prediction_research_duckduckgo_timeout_seconds=5.0,
        prediction_research_duckduckgo_max_results_per_query=7,
        prediction_research_duckduckgo_backend="duckduckgo,mojeek",
    )

    researcher = build_default_prediction_researcher(settings)

    assert isinstance(researcher, OpenRouterPredictionResearcher)
    assert researcher.search_tool.timeout_seconds == 5.0
    assert researcher.search_tool.max_results_limit == 7
    assert researcher.search_tool.backend == "duckduckgo,mojeek"
