"""核心功能：验证 refresh 接口的触发行为与基础返回结构。"""

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


def test_refresh_endpoint_seeds_matches_and_returns_sync_run_status():
    runtime_dir = _runtime_dir("refresh")
    fixture_path = runtime_dir / "schedule.json"
    fixture_path.write_text(
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
                        "status": "not_started",
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

    database_path = runtime_dir / "refresh.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        empty_matches = client.get("/api/matches")
        refresh_response = client.post("/api/refresh")
        seeded_matches = client.get("/api/matches")
        second_refresh_response = client.post("/api/refresh")
        reseeded_matches = client.get("/api/matches")

    assert empty_matches.status_code == 200
    assert empty_matches.json()["total"] == 0

    assert refresh_response.status_code == 202
    refresh_payload = refresh_response.json()
    assert refresh_payload["status"] == "completed"
    assert isinstance(refresh_payload["sync_run_id"], str)

    assert second_refresh_response.status_code == 202
    assert second_refresh_response.json()["status"] == "completed"

    assert seeded_matches.json()["total"] == 1
    assert reseeded_matches.json()["total"] == 1
