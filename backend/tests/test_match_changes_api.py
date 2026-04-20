"""核心功能：验证比赛字段变更历史查询接口的返回契约。"""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app
from backend.models.match import Match
from backend.models.match_change import MatchChange


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_match_changes_endpoint_returns_chronological_change_history():
    runtime_dir = _runtime_dir("match_changes_api")
    database_path = runtime_dir / "match_changes.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
        openrouter_model_config_path=None,
        openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as session:
            session.add(
                Match(
                    id="fwc2026-r32-001",
                    official_match_number=73,
                    kickoff_label="M073",
                    sort_order=73,
                    date="2026-06-28",
                    time="TBD",
                    stage="Round of 32",
                    group_name=None,
                    venue="TBD Stadium",
                    home_team={"name": "Mexico", "flag": "MX", "fifa_rank": 14, "form": []},
                    away_team={"name": "Japan", "flag": "JP", "fifa_rank": 18, "form": []},
                    status="finished",
                    score={"home": 2, "away": 1},
                    prediction=None,
                    head_to_head=None,
                    key_players={"home_injured": [], "away_suspended": []},
                    source_updated_at="2026-06-28T22:00:00Z",
                )
            )
            session.add_all(
                [
                    MatchChange(
                        match_id="fwc2026-r32-001",
                        sync_run_id="sync-1",
                        field_name="home_team",
                        old_value={"name": "Winner Group A"},
                        new_value={"name": "Mexico"},
                        change_type="filled",
                        changed_at="2026-06-26T00:00:00Z",
                    ),
                    MatchChange(
                        match_id="fwc2026-r32-001",
                        sync_run_id="sync-2",
                        field_name="score",
                        old_value=None,
                        new_value={"home": 2, "away": 1},
                        change_type="result_updated",
                        changed_at="2026-06-28T22:00:00Z",
                    ),
                ]
            )
            session.commit()

        response = client.get("/api/matches/fwc2026-r32-001/changes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["match_id"] == "fwc2026-r32-001"
    assert payload["total"] == 2
    assert [item["field_name"] for item in payload["items"]] == ["home_team", "score"]
    assert payload["items"][0]["change_type"] == "filled"
    assert payload["items"][1]["new_value"] == {"home": 2, "away": 1}
