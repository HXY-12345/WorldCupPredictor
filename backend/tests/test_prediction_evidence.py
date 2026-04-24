"""核心功能：验证 fake 与 OpenRouter evidence 阶段的结构化输出解析与容错行为。"""

import json
from pathlib import Path
import time
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterSettings
from backend.llm.provider import PredictionProviderTimeoutError
from backend.main import create_app
from backend.services.prediction_evidence import (
    OpenRouterPredictionEvidenceSynthesizer,
    synthesize_fake_prediction_evidence,
)
from backend.services.prediction_research import PredictionResearchArtifacts, run_fake_prediction_research


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


def _evidence_settings() -> OpenRouterSettings:
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


class SlowOpenRouterClient:
    def create_chat_completion(self, **kwargs):
        time.sleep(0.2)
        return {"choices": []}


def test_synthesize_fake_prediction_evidence_returns_expected_bundle_shape():
    runtime_dir = _runtime_dir("prediction_evidence")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence.db"
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
        evidence = synthesize_fake_prediction_evidence(
            app.state.session_factory,
            "fwc2026-m001",
            research,
        )

    assert evidence.synthesizer_model == "fake-evidence-v1"
    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert len(evidence.evidence_bundle["home_support"]) >= 1
    assert len(evidence.evidence_bundle["away_support"]) >= 1
    assert len(evidence.evidence_bundle["high_confidence_summary"]) >= 1
    assert evidence.evidence_bundle["conflicts"] == []


def test_openrouter_prediction_evidence_synthesizer_parses_structured_payload_and_forwards_request_settings():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": [{"topic": "preview", "query": "Mexico vs South Africa preview"}]},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[
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
        used_fallback_sources=False,
    )
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "match_id": "fwc2026-m001",
                                "home_support": ["主队近期状态更稳定。"],
                                "away_support": ["客队仍有一定反击速度。"],
                                "neutral_factors": ["比赛仍处于赛前阶段。"],
                                "market_view": ["市场稍微偏向主队，但不能单独依赖。"],
                                "conflicts": ["部分报道对首发阵容判断不一致。"],
                                "high_confidence_summary": ["主队略占优，但优势有限。"],
                                "document_titles": ["Mexico vs South Africa preview"],
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(_evidence_settings(), client=client)
        evidence = synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)

    assert evidence.synthesizer_model == "qwen/qwen3.5-flash-02-23"
    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert evidence.evidence_bundle["conflicts"] == ["部分报道对首发阵容判断不一致。"]
    assert client.calls[0]["plugins"] == [{"id": "response-healing"}]
    assert client.calls[0]["provider"] == {"require_parameters": True}
    assert "Mexico vs South Africa preview" in client.calls[0]["messages"][1]["content"]


def test_openrouter_prediction_evidence_synthesizer_tolerates_non_list_fields():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter_fuzzy")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter_fuzzy.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": []},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[],
        used_fallback_sources=False,
    )
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "match_id": ["unexpected-shape"],
                                "home_support": "主队近期状态更稳定",
                                "away_support": {"bad": "shape"},
                                "neutral_factors": None,
                                "market_view": "市场稍微偏向主队",
                                "conflicts": ["伤停信息仍有分歧"],
                                "high_confidence_summary": "主队略占优，但优势有限",
                                "document_titles": "Preview",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(_evidence_settings(), client=client)
        evidence = synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)

    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert evidence.evidence_bundle["home_support"] == ["主队近期状态更稳定"]
    assert evidence.evidence_bundle["away_support"] == []
    assert evidence.evidence_bundle["neutral_factors"] == []
    assert evidence.evidence_bundle["market_view"] == ["市场稍微偏向主队"]
    assert evidence.evidence_bundle["high_confidence_summary"] == ["主队略占优，但优势有限"]
    assert evidence.evidence_bundle["document_titles"] == ["Preview"]


def test_openrouter_prediction_evidence_synthesizer_extracts_json_from_wrapped_text():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter_wrapped")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter_wrapped.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": []},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[],
        used_fallback_sources=False,
    )
    wrapped_payload = {
        "match_id": "fwc2026-m001",
        "home_support": ["home team form looks steadier"],
        "away_support": ["away team still has transition threat"],
        "neutral_factors": ["the match is still pre-kickoff"],
        "market_view": ["market slightly leans to the home team"],
        "conflicts": [],
        "high_confidence_summary": ["home side has a small edge"],
        "document_titles": ["Preview"],
    }
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": "wrapped payload follows\n```json\n"
                        + json.dumps(wrapped_payload, ensure_ascii=False)
                        + "\n```",
                    }
                }
            ],
        }
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(_evidence_settings(), client=client)
        evidence = synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)

    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert evidence.evidence_bundle["home_support"] == ["home team form looks steadier"]


def test_openrouter_prediction_evidence_synthesizer_normalizes_analysis_style_payload():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter_analysis_style")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter_analysis_style.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": []},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[
            {
                "title": "Mexico vs South Africa preview",
                "url": "https://example.com/preview",
                "domain": "example.com",
                "content_text": "Preview text",
            }
        ],
        used_fallback_sources=False,
    )
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "match_id": "fwc2026-m001",
                                "high_confidence_summary": "Mexico has the stronger base case.",
                                "evidence_analysis": {
                                    "home_advantage": "Mexico has home advantage.",
                                    "away_analysis": "South Africa has inconsistent recent form.",
                                    "neutral_factors": "Head-to-head history is mixed.",
                                },
                                "uncertainties": ["Lineups remain uncertain."],
                                "market_view": "Market slightly leans home.",
                                "source_conflicts": ["Kickoff date needs official confirmation."],
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(_evidence_settings(), client=client)
        evidence = synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)

    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert evidence.evidence_bundle["home_support"] == ["Mexico has home advantage."]
    assert evidence.evidence_bundle["away_support"] == ["South Africa has inconsistent recent form."]
    assert evidence.evidence_bundle["neutral_factors"] == ["Head-to-head history is mixed."]
    assert evidence.evidence_bundle["market_view"] == ["Market slightly leans home."]
    assert evidence.evidence_bundle["conflicts"] == [
        "Lineups remain uncertain.",
        "Kickoff date needs official confirmation.",
    ]
    assert evidence.evidence_bundle["high_confidence_summary"] == ["Mexico has the stronger base case."]
    assert evidence.evidence_bundle["document_titles"] == ["Mexico vs South Africa preview"]


def test_openrouter_prediction_evidence_synthesizer_normalizes_nested_bundle_payload():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter_nested_bundle")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter_nested_bundle.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": []},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[
            {
                "title": "FOX Sports preview",
                "url": "https://www.foxsports.com/example",
                "domain": "www.foxsports.com",
                "content_text": "Preview text",
            }
        ],
        used_fallback_sources=False,
    )
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "match_id": "fwc2026-m001",
                                "evidence_bundle": {
                                    "match_logistics": {
                                        "date": "June 11, 2026",
                                        "venue": "Mexico City (Azteca Stadium)",
                                        "group": "Group A",
                                    },
                                    "team_profiles": {
                                        "mexico": {
                                            "coach": "Javier Aguirre",
                                            "recent_form": "DDWWW",
                                        },
                                        "south_africa": {
                                            "coach": "Hugo Broos",
                                            "recent_form": "LDLWL",
                                        },
                                    },
                                    "historical_h2h": [
                                        {
                                            "year": 2010,
                                            "tournament": "World Cup",
                                            "result": "1-1 draw",
                                        }
                                    ],
                                },
                                "sources": [
                                    {
                                        "domain": "www.foxsports.com",
                                        "url": "https://www.foxsports.com/example",
                                    }
                                ],
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(_evidence_settings(), client=client)
        evidence = synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)

    assert evidence.evidence_bundle["match_id"] == "fwc2026-m001"
    assert any("Javier Aguirre" in item for item in evidence.evidence_bundle["home_support"])
    assert any("Hugo Broos" in item for item in evidence.evidence_bundle["away_support"])
    assert any("June 11, 2026" in item for item in evidence.evidence_bundle["neutral_factors"])
    assert "www.foxsports.com" in evidence.evidence_bundle["document_titles"]


def test_openrouter_prediction_evidence_synthesizer_raises_timeout_when_client_hangs():
    runtime_dir = _runtime_dir("prediction_evidence_openrouter_timeout")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_evidence_openrouter_timeout.db"
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
    research = PredictionResearchArtifacts(
        planner_model="qwen/qwen3.5-flash-02-23",
        search_plan={"queries": []},
        search_trace={"completed": True, "round_count": 1},
        search_documents=[],
        used_fallback_sources=False,
    )

    with TestClient(app):
        synthesizer = OpenRouterPredictionEvidenceSynthesizer(
            _evidence_settings(),
            client=SlowOpenRouterClient(),
            timeout_seconds=0.01,
        )
        started_at = time.perf_counter()
        with pytest.raises(PredictionProviderTimeoutError):
            synthesizer.synthesize(app.state.session_factory, "fwc2026-m001", research)
        elapsed = time.perf_counter() - started_at

    assert elapsed < 0.1
