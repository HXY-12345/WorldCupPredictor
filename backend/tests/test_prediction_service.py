"""核心功能：验证预测服务可以消费 provider 输出并写入预测历史。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterSettings
from backend.llm.openrouter_prediction import OpenRouterPredictionProvider
from backend.main import create_app
from backend.models.prediction_version import PredictionVersion
from backend.services.predictions import MatchNotPredictableError, create_prediction
from backend.services.prediction_schema import PredictionSchemaError


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_fixture(path: Path, *, status: str = "not_started") -> None:
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
                        "home_team": {
                            "name": "Mexico",
                            "flag": "MX",
                            "fifa_rank": 12,
                            "form": ["W", "D", "W"],
                        },
                        "away_team": {
                            "name": "South Africa",
                            "flag": "ZA",
                            "fifa_rank": 47,
                            "form": ["D", "L", "W"],
                        },
                        "status": status,
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


class StaticPredictionProvider:
    def predict(self, request):
        match_facts = request.metadata["match_facts"]
        return {
            "predicted_score": {"home": 3, "away": 1},
            "outcome_pick": "home_win",
            "home_goals_pick": 3,
            "away_goals_pick": 1,
            "total_goals_pick": 4,
            "confidence": 83,
            "reasoning_summary": f"Static provider prediction for {match_facts['match_id']}.",
            "evidence_items": [
                {
                    "claim": "Mexico has stronger recent form.",
                    "source_name": "form",
                    "source_url": "https://example.com/form",
                    "source_level": 2,
                },
                {
                    "claim": "Mexico City venue favors the home side.",
                    "source_name": "venue",
                    "source_url": "https://example.com/venue",
                    "source_level": 3,
                },
                {
                    "claim": "South Africa defensive record is mixed.",
                    "source_name": "defense",
                    "source_url": "https://example.com/defense",
                    "source_level": 2,
                },
            ],
            "uncertainties": ["Lineup is not fully confirmed."],
            "model_meta": {
                "provider": "static-test",
                "model_name": "static-test-model",
                "predicted_at": "2026-04-19T12:00:00Z",
            },
            "input_snapshot": match_facts,
        }


class BrokenPredictionProvider:
    def predict(self, request):
        return {"predicted_score": {"home": 1, "away": 0}}


class DummyOpenRouterClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        return self.payload


def _openrouter_prediction_payload() -> dict:
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
    }


def test_create_prediction_persists_provider_output_and_history():
    runtime_dir = _runtime_dir("prediction_service")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_service.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        prediction = create_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            provider=StaticPredictionProvider(),
        )

    assert prediction["confidence"] == 83
    assert prediction["model_meta"]["provider"] == "static-test"

    with app.state.session_factory() as session:
        versions = session.scalars(
            select(PredictionVersion).order_by(PredictionVersion.version_no.asc())
        ).all()

    assert len(versions) == 1
    assert versions[0].model_name == "static-test-model"
    assert versions[0].prediction["predicted_score"]["home"] == 3


def test_create_prediction_rejects_invalid_provider_output_without_persisting():
    runtime_dir = _runtime_dir("prediction_service_invalid")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_service_invalid.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        try:
            create_prediction(
                app.state.session_factory,
                "fwc2026-m001",
                provider=BrokenPredictionProvider(),
            )
        except PredictionSchemaError:
            pass
        else:
            raise AssertionError("Expected invalid provider output to raise PredictionSchemaError.")

    with app.state.session_factory() as session:
        version_count = session.scalar(select(func.count()).select_from(PredictionVersion))

    assert version_count == 0


def test_create_prediction_rejects_started_matches():
    runtime_dir = _runtime_dir("prediction_service_started")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path, status="finished")
    database_path = runtime_dir / "prediction_service_started.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        try:
            create_prediction(
                app.state.session_factory,
                "fwc2026-m001",
                provider=StaticPredictionProvider(),
            )
        except MatchNotPredictableError:
            pass
        else:
            raise AssertionError("Expected finished match to be rejected.")


def test_create_prediction_uses_openrouter_provider_request_settings():
    runtime_dir = _runtime_dir("prediction_service_openrouter_request")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_service_openrouter_request.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)
    client = DummyOpenRouterClient(
        payload={
            "model": "qwen/qwen3.5-flash-20260224",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(_openrouter_prediction_payload(), ensure_ascii=False),
                    }
                }
            ],
        }
    )
    provider = OpenRouterPredictionProvider(
        OpenRouterSettings(
            base_url="https://openrouter.ai/api/v1/chat/completions",
            model="qwen/qwen3.5-flash-20260224",
            api_key="sk-or-v1-test-key",
            enable_web_plugin=False,
            enable_response_healing=False,
            require_parameters=False,
        ),
        client=client,
    )

    with TestClient(app):
        create_prediction(app.state.session_factory, "fwc2026-m001", provider=provider)

    assert client.calls[0]["plugins"] == []
    assert client.calls[0]["provider"] == {"require_parameters": False}
    assert client.calls[0]["response_format"] is None
