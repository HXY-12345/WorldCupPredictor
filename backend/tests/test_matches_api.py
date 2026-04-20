"""核心功能：验证比赛列表接口的排序与基础字段契约。"""

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


def test_matches_endpoint_returns_seeded_matches_sorted_by_date_and_order():
    runtime_dir = _runtime_dir("matches")
    fixture_path = runtime_dir / "schedule.json"
    fixture_path.write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "id": "fwc2026-m002",
                        "official_match_number": 2,
                        "kickoff_label": "M002",
                        "sort_order": 2,
                        "date": "2026-06-12",
                        "time": "TBD",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Toronto Stadium",
                        "home_team": {
                            "name": "Canada",
                            "flag": "CA",
                            "fifa_rank": None,
                            "form": [],
                        },
                        "away_team": {
                            "name": "Japan",
                            "flag": "JP",
                            "fifa_rank": None,
                            "form": [],
                        },
                        "status": "not_started",
                        "score": None,
                        "prediction": {
                            "home_score": 2,
                            "away_score": 1,
                            "confidence": 74,
                            "probabilities": {
                                "home_win": 49,
                                "draw": 28,
                                "away_win": 23,
                            },
                            "reasoning": "Seeded prediction",
                            "predicted_at": "2026-04-18T00:00:00Z",
                        },
                        "head_to_head": None,
                        "key_players": {
                            "home_injured": [],
                            "away_suspended": [],
                        },
                    },
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
                    },
                ],
                "last_updated": "2026-03-31T00:00:00Z",
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    database_path = runtime_dir / "matches.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/matches")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert payload["last_updated"] == "2026-03-31T00:00:00Z"
    assert [match["id"] for match in payload["matches"]] == [
        "fwc2026-m001",
        "fwc2026-m002",
    ]
    assert payload["matches"][0]["home_team"]["name"] == "Mexico"
    assert payload["matches"][1]["prediction"]["confidence"] == 74
