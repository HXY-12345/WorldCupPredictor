"""核心功能：验证预测上下文从数据库事实与历史版本中正确组装。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.core.config import Settings
from backend.main import create_app
from backend.models.prediction_version import PredictionVersion
from backend.services.prediction_context import build_prediction_context


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


def test_build_prediction_context_exposes_match_facts_without_prediction_history():
    runtime_dir = _runtime_dir("prediction_context")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_context.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        with app.state.session_factory() as session:
            session.add(
                PredictionVersion(
                    match_id="fwc2026-m001",
                    version_no=1,
                    created_at="2026-04-19T12:00:00Z",
                    model_name="seeded-default",
                    prediction={
                        "predicted_score": {"home": 1, "away": 0},
                        "outcome_pick": "home_win",
                        "home_goals_pick": 1,
                        "away_goals_pick": 0,
                        "total_goals_pick": 1,
                        "confidence": 68,
                        "reasoning_summary": "Seeded prediction",
                        "evidence_items": [],
                        "uncertainties": [],
                        "model_meta": {
                            "provider": "seed",
                            "model_name": "seeded-default",
                            "predicted_at": "2026-04-19T12:00:00Z",
                        },
                        "input_snapshot": {
                            "match_id": "fwc2026-m001",
                            "date": "2026-06-11",
                            "time": "18:00",
                            "stage": "Group Stage",
                            "group_name": "A",
                            "venue": "Mexico City Stadium",
                            "home_team": {"name": "Mexico", "flag": "MX"},
                            "away_team": {"name": "South Africa", "flag": "ZA"},
                        },
                    },
                )
            )
            session.commit()

        context = build_prediction_context(app.state.session_factory, "fwc2026-m001")

    assert context.match_facts["match_id"] == "fwc2026-m001"
    assert context.match_facts["home_team"]["name"] == "Mexico"
    assert "prediction" not in context.match_facts
    assert context.database_context == {}


def test_build_prediction_context_rejects_missing_match():
    runtime_dir = _runtime_dir("prediction_context_missing")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_context_missing.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        with app.state.session_factory() as session:
            match_count = session.scalar(select(func.count()).select_from(PredictionVersion))

        assert match_count == 0

        try:
            build_prediction_context(app.state.session_factory, "missing-match")
        except KeyError:
            pass
        else:
            raise AssertionError("Expected build_prediction_context to reject missing match.")
