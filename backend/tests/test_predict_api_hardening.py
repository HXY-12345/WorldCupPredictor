"""核心功能：验证预测 API 的 provider 失败处理与并发保护行为。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.llm.provider import PredictionProviderResponseError
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


class ExplodingPredictionProvider:
    def predict(self, request):
        raise PredictionProviderResponseError("Upstream prediction provider failed.")


class BusyPredictionGuard:
    def acquire(self, match_id: str) -> bool:
        return False

    def release(self, match_id: str) -> None:
        return None


def test_predict_endpoint_returns_502_when_provider_fails():
    runtime_dir = _runtime_dir("predict_api_provider_failure")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "predict_api_provider_failure.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings, prediction_provider=ExplodingPredictionProvider())

    with TestClient(app) as client:
        response = client.post("/api/predict/fwc2026-m001")

    assert response.status_code == 502


def test_predict_endpoint_returns_409_when_prediction_is_already_running():
    runtime_dir = _runtime_dir("predict_api_busy")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "predict_api_busy.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings, prediction_guard=BusyPredictionGuard())

    with TestClient(app) as client:
        response = client.post("/api/predict/fwc2026-m001")

    assert response.status_code == 409
    assert "already running" in response.json()["detail"].lower()
