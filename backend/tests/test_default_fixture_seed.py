"""核心功能：验证默认 fixture 可以导入并纠正世界杯官方赛程基线数据。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.database.session import create_session_factory, init_database
from backend.main import create_app
from backend.models.match import Match


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_default_fixture_seed_populates_official_schedule():
    runtime_dir = _runtime_dir("default_seed")
    database_path = runtime_dir / "worldcup.db"
    settings = Settings(database_url=f"sqlite:///{database_path}")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/matches")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] >= 100
    assert payload["matches"][0]["id"].startswith("fwc2026-m")
    assert payload["matches"][0]["date"] == "2026-06-12"
    assert payload["matches"][0]["time"] == "03:00"
    assert payload["matches"][-1]["date"] == "2026-07-20"


def test_default_fixture_seed_reconciles_existing_database_to_official_schedule():
    runtime_dir = _runtime_dir("default_seed_reconcile")
    database_path = runtime_dir / "worldcup.db"
    fixture_path = runtime_dir / "official_schedule.json"
    fixture_payload = {
        "last_updated": "2026-04-21T00:00:00Z",
        "matches": [
            {
                "id": "fwc2026-m001",
                "official_match_number": 1,
                "kickoff_label": "M001",
                "sort_order": 1,
                "date": "2026-06-12",
                "time": "03:00",
                "stage": "Group Stage",
                "group": "A",
                "venue": "Mexico City Stadium",
                "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
                "status": "not_started",
                "score": None,
                "prediction": None,
                "head_to_head": None,
                "key_players": {"home_injured": [], "away_suspended": []},
            },
            {
                "id": "fwc2026-m002",
                "official_match_number": 2,
                "kickoff_label": "M002",
                "sort_order": 2,
                "date": "2026-06-12",
                "time": "10:00",
                "stage": "Group Stage",
                "group": "A",
                "venue": "Estadio Guadalajara",
                "home_team": {"name": "Korea Republic", "flag": "KR", "fifa_rank": None, "form": []},
                "away_team": {"name": "Czechia", "flag": "CZ", "fifa_rank": None, "form": []},
                "status": "not_started",
                "score": None,
                "prediction": None,
                "head_to_head": None,
                "key_players": {"home_injured": [], "away_suspended": []},
            },
        ],
    }
    fixture_path.write_text(json.dumps(fixture_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    engine, session_factory = create_session_factory(f"sqlite:///{database_path}")
    init_database(engine)
    with session_factory() as session:
        session.add_all(
            [
                Match(
                    id="fwc2026-m001",
                    official_match_number=1,
                    kickoff_label="M001",
                    sort_order=1,
                    date="2026-06-11",
                    time="21:00",
                    stage="Group Stage",
                    group_name="A",
                    venue="Mexico City Stadium",
                    home_team={"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                    away_team={"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
                    status="not_started",
                    score=None,
                    prediction=None,
                    head_to_head=None,
                    key_players={"home_injured": [], "away_suspended": []},
                    source_updated_at="2026-04-20T16:30:18.961Z",
                ),
                Match(
                    id="fwc2026-m002",
                    official_match_number=2,
                    kickoff_label="M002",
                    sort_order=2,
                    date="2026-06-11",
                    time="18:00",
                    stage="Group Stage",
                    group_name="A",
                    venue="Estadio Guadalajara",
                    home_team={"name": "Korea Republic", "flag": "KR", "fifa_rank": None, "form": []},
                    away_team={"name": "Czechia", "flag": "CZ", "fifa_rank": None, "form": []},
                    status="not_started",
                    score=None,
                    prediction=None,
                    head_to_head=None,
                    key_players={"home_injured": [], "away_suspended": []},
                    source_updated_at="2026-04-20T16:30:18.961Z",
                ),
                Match(
                    id="fwc2026-m1000",
                    official_match_number=1000,
                    kickoff_label="M1000",
                    sort_order=1000,
                    date="2026-06-20",
                    time="08:00",
                    stage="Group Stage",
                    group_name="X",
                    venue="Rogue Stadium",
                    home_team={"name": "Team A", "flag": "AA", "fifa_rank": None, "form": []},
                    away_team={"name": "Team B", "flag": "BB", "fifa_rank": None, "form": []},
                    status="not_started",
                    score=None,
                    prediction=None,
                    head_to_head=None,
                    key_players={"home_injured": [], "away_suspended": []},
                    source_updated_at="2026-04-20T16:30:18.961Z",
                ),
            ]
        )
        session.commit()
    engine.dispose()

    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/matches")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert [item["id"] for item in payload["matches"]] == ["fwc2026-m001", "fwc2026-m002"]
    assert payload["matches"][0]["date"] == "2026-06-12"
    assert payload["matches"][0]["time"] == "03:00"
    assert payload["matches"][1]["date"] == "2026-06-12"
    assert payload["matches"][1]["time"] == "10:00"
