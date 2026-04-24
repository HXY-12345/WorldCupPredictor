"""核心功能：验证 prediction_runs 查询接口可读取单场比赛的预测执行记录与详情。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app


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
                        "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": 12, "form": ["W"]},
                        "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": 47, "form": ["L"]},
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


class StaticPredictionProvider:
    def predict(self, request):
        match_facts = request.metadata["match_facts"]
        return {
            "predicted_score": {"home": 2, "away": 1},
            "outcome_pick": "home_win",
            "home_goals_pick": 2,
            "away_goals_pick": 1,
            "total_goals_pick": 3,
            "confidence": 76,
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


def test_prediction_runs_api_returns_match_scoped_runs_and_detail():
    runtime_dir = _runtime_dir("prediction_runs_api")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_runs_api.db"
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
        predict_response = client.post("/api/predict/fwc2026-m001")
        runs_response = client.get("/api/matches/fwc2026-m001/prediction-runs")

        assert predict_response.status_code == 200
        assert runs_response.status_code == 200

        runs_payload = runs_response.json()
        run_id = runs_payload["items"][0]["id"]
        detail_response = client.get(f"/api/prediction-runs/{run_id}")

    assert runs_payload["total"] == 1
    assert runs_payload["items"][0]["match_id"] == "fwc2026-m001"
    assert runs_payload["items"][0]["status"] == "succeeded"
    assert runs_payload["items"][0]["prediction_version_id"] is not None
    assert runs_payload["items"][0]["planner_model"] == "fake-research-v1"
    assert runs_payload["items"][0]["synthesizer_model"] == "fake-evidence-v1"
    assert runs_payload["items"][0]["decider_model"] == "static-test-model"
    assert runs_payload["items"][0]["document_count"] >= 4
    assert runs_payload["items"][0]["is_full_live_chain"] is False
    assert runs_payload["items"][0]["has_any_fallback"] is True

    detail_payload = detail_response.json()
    assert detail_response.status_code == 200
    assert detail_payload["id"] == run_id
    assert detail_payload["match_id"] == "fwc2026-m001"
    assert detail_payload["status"] == "succeeded"
    assert detail_payload["search_plan_json"] is not None
    assert detail_payload["search_trace_json"] is not None
    assert detail_payload["search_documents_json"] is not None
    assert len(detail_payload["search_documents_json"]) >= 4
    assert detail_payload["search_trace_json"]["generated_from_match_facts"] is True
    assert detail_payload["search_trace_json"]["fallback_mode"] == "local_match_fact_synthesis"
    assert detail_payload["evidence_bundle_json"] is not None
    assert detail_payload["stage_trace_json"]["research"]["mode"] == "fallback"
    assert detail_payload["stage_trace_json"]["evidence"]["mode"] == "fallback"
    assert detail_payload["stage_trace_json"]["decider"]["mode"] == "live"
    assert detail_payload["stage_trace_json"]["decider"]["model_name"] == "static-test-model"



def test_prediction_runs_api_returns_404_for_unknown_match():
    runtime_dir = _runtime_dir("prediction_runs_api_missing_match")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_runs_api_missing_match.db"
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
        response = client.get("/api/matches/unknown-match/prediction-runs")

    assert response.status_code == 404
