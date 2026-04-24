"""核心功能：验证预测接口的生成逻辑、历史版本与开赛限制。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.core.config import Settings
from backend.main import create_app
from backend.models.prediction_version import PredictionVersion


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
                        "time": "TBD",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {
                            "name": "Mexico",
                            "flag": "MX",
                            "fifa_rank": None,
                            "form": [],
                        },
                        "away_team": {
                            "name": "South Africa",
                            "flag": "ZA",
                            "fifa_rank": None,
                            "form": [],
                        },
                        "status": status,
                        "score": None,
                        "prediction": {
                            "home_score": 1,
                            "away_score": 0,
                            "confidence": 68,
                            "probabilities": {
                                "home_win": 55,
                                "draw": 25,
                                "away_win": 20,
                            },
                            "reasoning": "Seeded prediction",
                            "predicted_at": "2026-04-18T00:00:00Z",
                        },
                        "head_to_head": None,
                        "key_players": {
                            "home_injured": [],
                            "away_suspended": [],
                        },
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
            "predicted_score": {"home": 2, "away": 1},
            "outcome_pick": "home_win",
            "home_goals_pick": 2,
            "away_goals_pick": 1,
            "total_goals_pick": 3,
            "confidence": 68,
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


def test_predict_endpoint_returns_prediction_and_persists_version_history():
    runtime_dir = _runtime_dir("predict")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "predict.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings, prediction_provider=StaticPredictionProvider())

    with TestClient(app) as client:
        first_response = client.post("/api/predict/fwc2026-m001")
        second_response = client.post("/api/predict/fwc2026-m001")
        matches_response = client.get("/api/matches")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_payload = first_response.json()
    second_payload = second_response.json()
    matches_payload = matches_response.json()

    assert first_payload["match_id"] == "fwc2026-m001"
    assert first_payload["cached"] is False
    assert first_payload["prediction"]["confidence"] == 68
    assert second_payload["prediction"]["confidence"] == 68
    assert matches_payload["matches"][0]["prediction"]["confidence"] == 68

    with app.state.session_factory() as session:
        versions = session.scalars(
            select(PredictionVersion).order_by(PredictionVersion.version_no.asc())
        ).all()

    assert [version.version_no for version in versions] == [1, 2]
    assert versions[0].match_id == "fwc2026-m001"


def test_predict_endpoint_returns_502_when_decider_provider_is_not_configured():
    runtime_dir = _runtime_dir("predict_missing_provider")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "predict_missing_provider.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/predict/fwc2026-m001")

    assert response.status_code == 502
    assert "decider" in response.json()["detail"].lower()


def test_predict_endpoint_rejects_matches_that_have_started():
    runtime_dir = _runtime_dir("predict_started")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path, status="finished")
    database_path = runtime_dir / "predict_started.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/predict/fwc2026-m001")

    assert response.status_code == 409
