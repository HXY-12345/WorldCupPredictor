"""核心功能：验证赛后评估规则、赛前最后一版预测选择与评估状态落库行为。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.core.config import Settings
from backend.main import create_app
from backend.models.match_evaluation import MatchEvaluation
from backend.models.prediction_version import PredictionVersion
from backend.evaluation.scorer import score_prediction
from backend.evaluation.service import evaluate_match


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_fixture(path: Path, *, status: str = "finished", score: dict | None = None) -> None:
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
                        "score": score,
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-06-11T22:00:00Z",
                "total": 1,
            }
        ),
        encoding="utf-8",
    )


def _prediction_payload(home: int, away: int, predicted_at: str) -> dict:
    if home > away:
        outcome_pick = "home_win"
    elif home < away:
        outcome_pick = "away_win"
    else:
        outcome_pick = "draw"

    return {
        "predicted_score": {"home": home, "away": away},
        "outcome_pick": outcome_pick,
        "home_goals_pick": home,
        "away_goals_pick": away,
        "total_goals_pick": home + away,
        "confidence": 80,
        "reasoning_summary": "Structured test prediction.",
        "evidence_items": [
            {
                "claim": "Evidence 1",
                "source_name": "form",
                "source_url": "https://example.com/form",
                "source_level": 2,
            },
            {
                "claim": "Evidence 2",
                "source_name": "injury",
                "source_url": "https://example.com/injury",
                "source_level": 2,
            },
            {
                "claim": "Evidence 3",
                "source_name": "venue",
                "source_url": "https://example.com/venue",
                "source_level": 3,
            },
        ],
        "uncertainties": [],
        "model_meta": {
            "provider": "static-test",
            "model_name": "static-test-model",
            "predicted_at": predicted_at,
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


def test_score_prediction_assigns_core_partial_and_miss_grades():
    exact = score_prediction(_prediction_payload(2, 1, "2026-06-11T17:00:00Z"), actual_home_score=2, actual_away_score=1)
    partial = score_prediction(
        _prediction_payload(1, 1, "2026-06-11T17:00:00Z"),
        actual_home_score=2,
        actual_away_score=1,
    )
    miss = score_prediction(_prediction_payload(0, 0, "2026-06-11T17:00:00Z"), actual_home_score=2, actual_away_score=1)

    assert exact["exact_score_hit"] is True
    assert exact["outcome_hit"] is True
    assert exact["home_goals_hit"] is True
    assert exact["away_goals_hit"] is True
    assert exact["total_goals_hit"] is True
    assert exact["grade"] == "core_hit"

    assert partial["exact_score_hit"] is False
    assert partial["outcome_hit"] is False
    assert partial["home_goals_hit"] is False
    assert partial["away_goals_hit"] is True
    assert partial["total_goals_hit"] is False
    assert partial["grade"] == "partial_hit"

    assert miss["exact_score_hit"] is False
    assert miss["outcome_hit"] is False
    assert miss["home_goals_hit"] is False
    assert miss["away_goals_hit"] is False
    assert miss["total_goals_hit"] is False
    assert miss["grade"] == "miss"


def test_evaluate_match_uses_latest_pre_kickoff_prediction_version():
    runtime_dir = _runtime_dir("evaluation_latest_pre_kickoff")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path, status="finished", score={"home": 2, "away": 1})
    database_path = runtime_dir / "evaluation_latest_pre_kickoff.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        with app.state.session_factory() as session:
            session.add_all(
                [
                    PredictionVersion(
                        match_id="fwc2026-m001",
                        version_no=1,
                        created_at="2026-06-11T16:30:00Z",
                        model_name="static-test-model",
                        prediction=_prediction_payload(1, 0, "2026-06-11T16:30:00Z"),
                    ),
                    PredictionVersion(
                        match_id="fwc2026-m001",
                        version_no=2,
                        created_at="2026-06-11T17:59:00Z",
                        model_name="static-test-model",
                        prediction=_prediction_payload(2, 1, "2026-06-11T17:59:00Z"),
                    ),
                    PredictionVersion(
                        match_id="fwc2026-m001",
                        version_no=3,
                        created_at="2026-06-11T18:01:00Z",
                        model_name="static-test-model",
                        prediction=_prediction_payload(0, 0, "2026-06-11T18:01:00Z"),
                    ),
                ]
            )
            session.commit()

        payload = evaluate_match(app.state.session_factory, "fwc2026-m001")

        with app.state.session_factory() as session:
            evaluation = session.scalar(
                select(MatchEvaluation).where(MatchEvaluation.match_id == "fwc2026-m001")
            )

    assert payload["evaluation_status"] == "scored"
    assert payload["prediction_version_id"] == 2
    assert payload["exact_score_hit"] is True
    assert payload["grade"] == "core_hit"
    assert evaluation is not None
    assert evaluation.prediction_version_id == 2


def test_evaluate_match_records_no_prediction_when_finished_match_has_no_pre_kickoff_version():
    runtime_dir = _runtime_dir("evaluation_no_prediction")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path, status="finished", score={"home": 3, "away": 2})
    database_path = runtime_dir / "evaluation_no_prediction.db"
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
                    created_at="2026-06-11T18:05:00Z",
                    model_name="static-test-model",
                    prediction=_prediction_payload(2, 0, "2026-06-11T18:05:00Z"),
                )
            )
            session.commit()

        payload = evaluate_match(app.state.session_factory, "fwc2026-m001")

    assert payload["evaluation_status"] == "no_prediction"
    assert payload["prediction_version_id"] is None
    assert payload["actual_home_score"] == 3
    assert payload["actual_away_score"] == 2
    assert payload["grade"] is None


def test_evaluate_match_marks_pending_result_when_regular_time_score_is_missing():
    runtime_dir = _runtime_dir("evaluation_pending_result")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path, status="finished", score=None)
    database_path = runtime_dir / "evaluation_pending_result.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)

    with TestClient(app):
        payload = evaluate_match(app.state.session_factory, "fwc2026-m001")

    assert payload["evaluation_status"] == "pending_result"
    assert payload["prediction_version_id"] is None
    assert payload["actual_home_score"] is None
    assert payload["actual_away_score"] is None
    assert payload["grade"] is None
