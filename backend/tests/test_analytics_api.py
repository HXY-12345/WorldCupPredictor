"""核心功能：验证统计分析与评估查询接口的返回结构和统计口径。"""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app
from backend.models.match import Match
from backend.models.match_evaluation import MatchEvaluation


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_analytics_and_evaluations_endpoints_return_expected_rollups():
    runtime_dir = _runtime_dir("analytics_api")
    database_path = runtime_dir / "analytics_api.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as session:
            session.add_all(
                [
                    Match(
                        id="fwc2026-m001",
                        official_match_number=1,
                        kickoff_label="M001",
                        sort_order=1,
                        date="2026-06-11",
                        time="18:00",
                        stage="Group Stage",
                        group_name="A",
                        venue="Mexico City Stadium",
                        home_team={"name": "Mexico"},
                        away_team={"name": "South Africa"},
                        status="finished",
                        score={"home": 2, "away": 1},
                        prediction=None,
                        head_to_head=None,
                        key_players=None,
                        source_updated_at="2026-06-11T22:00:00Z",
                    ),
                    Match(
                        id="fwc2026-m002",
                        official_match_number=2,
                        kickoff_label="M002",
                        sort_order=2,
                        date="2026-06-12",
                        time="20:00",
                        stage="Group Stage",
                        group_name="A",
                        venue="Toronto Stadium",
                        home_team={"name": "Canada"},
                        away_team={"name": "Japan"},
                        status="finished",
                        score={"home": 1, "away": 1},
                        prediction=None,
                        head_to_head=None,
                        key_players=None,
                        source_updated_at="2026-06-12T22:00:00Z",
                    ),
                    Match(
                        id="fwc2026-m065",
                        official_match_number=65,
                        kickoff_label="M065",
                        sort_order=65,
                        date="2026-06-28",
                        time="18:00",
                        stage="Round of 32",
                        group_name=None,
                        venue="Los Angeles Stadium",
                        home_team={"name": "Winner Group A"},
                        away_team={"name": "Runner-up Group B"},
                        status="finished",
                        score={"home": 0, "away": 1},
                        prediction=None,
                        head_to_head=None,
                        key_players=None,
                        source_updated_at="2026-06-28T22:00:00Z",
                    ),
                    Match(
                        id="fwc2026-m066",
                        official_match_number=66,
                        kickoff_label="M066",
                        sort_order=66,
                        date="2026-06-29",
                        time="18:00",
                        stage="Round of 32",
                        group_name=None,
                        venue="Dallas Stadium",
                        home_team={"name": "Winner Group C"},
                        away_team={"name": "Runner-up Group D"},
                        status="in_progress",
                        score=None,
                        prediction=None,
                        head_to_head=None,
                        key_players=None,
                        source_updated_at="2026-06-29T19:00:00Z",
                    ),
                ]
            )
            session.add_all(
                [
                    MatchEvaluation(
                        match_id="fwc2026-m001",
                        prediction_version_id=11,
                        evaluation_status="scored",
                        actual_home_score=2,
                        actual_away_score=1,
                        outcome_hit=True,
                        exact_score_hit=True,
                        home_goals_hit=True,
                        away_goals_hit=True,
                        total_goals_hit=True,
                        grade="core_hit",
                        rule_version="v1",
                        evaluated_at="2026-06-11T22:05:00Z",
                    ),
                    MatchEvaluation(
                        match_id="fwc2026-m002",
                        prediction_version_id=None,
                        evaluation_status="no_prediction",
                        actual_home_score=1,
                        actual_away_score=1,
                        outcome_hit=None,
                        exact_score_hit=None,
                        home_goals_hit=None,
                        away_goals_hit=None,
                        total_goals_hit=None,
                        grade=None,
                        rule_version="v1",
                        evaluated_at="2026-06-12T22:05:00Z",
                    ),
                    MatchEvaluation(
                        match_id="fwc2026-m065",
                        prediction_version_id=12,
                        evaluation_status="scored",
                        actual_home_score=0,
                        actual_away_score=1,
                        outcome_hit=False,
                        exact_score_hit=False,
                        home_goals_hit=False,
                        away_goals_hit=False,
                        total_goals_hit=False,
                        grade="miss",
                        rule_version="v1",
                        evaluated_at="2026-06-28T22:05:00Z",
                    ),
                    MatchEvaluation(
                        match_id="fwc2026-m066",
                        prediction_version_id=None,
                        evaluation_status="pending_result",
                        actual_home_score=None,
                        actual_away_score=None,
                        outcome_hit=None,
                        exact_score_hit=None,
                        home_goals_hit=None,
                        away_goals_hit=None,
                        total_goals_hit=None,
                        grade=None,
                        rule_version="v1",
                        evaluated_at="2026-06-29T19:05:00Z",
                    ),
                ]
            )
            session.commit()

        summary_response = client.get("/api/analytics/summary")
        by_stage_response = client.get("/api/analytics/by-stage")
        evaluations_response = client.get("/api/evaluations")
        evaluation_detail_response = client.get("/api/evaluations/fwc2026-m001")

    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["total_scored_matches"] == 2
    assert summary_payload["no_prediction_matches"] == 1
    assert summary_payload["pending_result_matches"] == 1
    assert summary_payload["dimensions"]["outcome"]["hit"] == 1
    assert summary_payload["dimensions"]["outcome"]["rate"] == 0.5
    assert summary_payload["dimensions"]["exact_score"]["hit"] == 1
    assert summary_payload["dimensions"]["total_goals"]["hit"] == 1
    assert summary_payload["grade_distribution"] == {
        "core_hit": 1,
        "partial_hit": 0,
        "miss": 1,
    }

    assert by_stage_response.status_code == 200
    by_stage_payload = by_stage_response.json()
    assert by_stage_payload["total"] == 2
    assert by_stage_payload["items"][0]["stage"] == "Group Stage"
    assert by_stage_payload["items"][0]["total_scored_matches"] == 1
    assert by_stage_payload["items"][0]["no_prediction_matches"] == 1
    assert by_stage_payload["items"][0]["dimensions"]["outcome"]["rate"] == 1.0
    assert by_stage_payload["items"][1]["stage"] == "Round of 32"
    assert by_stage_payload["items"][1]["total_scored_matches"] == 1
    assert by_stage_payload["items"][1]["pending_result_matches"] == 1
    assert by_stage_payload["items"][1]["grade_distribution"]["miss"] == 1

    assert evaluations_response.status_code == 200
    evaluations_payload = evaluations_response.json()
    assert evaluations_payload["total"] == 4
    assert evaluations_payload["items"][0]["match_id"] == "fwc2026-m001"
    assert evaluations_payload["items"][0]["stage"] == "Group Stage"

    assert evaluation_detail_response.status_code == 200
    evaluation_detail_payload = evaluation_detail_response.json()
    assert evaluation_detail_payload["match_id"] == "fwc2026-m001"
    assert evaluation_detail_payload["evaluation_status"] == "scored"
    assert evaluation_detail_payload["grade"] == "core_hit"
