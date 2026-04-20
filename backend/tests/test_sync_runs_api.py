"""核心功能：验证同步任务列表、同步详情与解析结果详情接口的返回结构和真实刷新联动表现。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app
from backend.models.match import Match
from backend.models.match_change import MatchChange
from backend.models.parse_output import ParseOutput
from backend.models.source_snapshot import SourceSnapshot
from backend.models.sync_run import SyncRun


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_sync_runs_and_parse_outputs_detail_endpoints_return_auditable_payloads():
    runtime_dir = _runtime_dir("sync_runs_api")
    database_path = runtime_dir / "sync_runs.db"
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
                    id="fwc2026-m001",
                    official_match_number=1,
                    kickoff_label="M001",
                    sort_order=1,
                    date="2026-06-11",
                    time="18:00",
                    stage="Group Stage",
                    group_name="A",
                    venue="Mexico City Stadium",
                    home_team={"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                    away_team={"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
                    status="finished",
                    score={"home": 2, "away": 1},
                    prediction=None,
                    head_to_head=None,
                    key_players={"home_injured": [], "away_suspended": []},
                    source_updated_at="2026-06-11T22:00:00Z",
                )
            )
            session.add_all(
                [
                    SyncRun(
                        id="sync-older",
                        trigger_type="manual",
                        status="completed",
                        started_at="2026-06-11T22:00:00Z",
                        finished_at="2026-06-11T22:02:00Z",
                        source_name="fifa_article",
                        error_message=None,
                    ),
                    SyncRun(
                        id="sync-latest",
                        trigger_type="manual",
                        status="completed",
                        started_at="2026-06-12T22:00:00Z",
                        finished_at="2026-06-12T22:02:00Z",
                        source_name="fifa_article,fifa_schedule_pdf",
                        error_message=None,
                    ),
                ]
            )
            session.add(
                SourceSnapshot(
                    sync_run_id="sync-latest",
                    source_name="fifa_article",
                    source_url="https://www.fifa.com/article",
                    content_type="text/html",
                    raw_body="<html>article</html>",
                    extracted_text="article",
                )
            )
            session.add(
                ParseOutput(
                    sync_run_id="sync-latest",
                    model_name="qwen/qwen3.5-flash-20260224",
                    parser_version="openrouter-chat-completions-v1",
                    structured_data={
                        "matches": [{"id": "fwc2026-m001"}],
                        "last_updated": "2026-06-12T22:00:00Z",
                        "total": 1,
                    },
                    raw_response=json.dumps({"id": "chatcmpl-test"}),
                )
            )
            session.add(
                MatchChange(
                    match_id="fwc2026-m001",
                    sync_run_id="sync-latest",
                    field_name="score",
                    old_value=None,
                    new_value={"home": 2, "away": 1},
                    change_type="result_updated",
                    changed_at="2026-06-12T22:01:00Z",
                )
            )
            session.commit()

        sync_runs_response = client.get("/api/sync-runs")
        sync_run_detail_response = client.get("/api/sync-runs/sync-latest")
        parse_output_detail_response = client.get("/api/parse-outputs/1")

    assert sync_runs_response.status_code == 200
    sync_runs_payload = sync_runs_response.json()
    assert sync_runs_payload["total"] == 2
    assert [item["id"] for item in sync_runs_payload["items"]] == ["sync-latest", "sync-older"]
    assert sync_runs_payload["items"][0]["parse_output_count"] == 1
    assert sync_runs_payload["items"][0]["source_snapshot_count"] == 1
    assert sync_runs_payload["items"][0]["match_change_count"] == 1

    assert sync_run_detail_response.status_code == 200
    sync_run_detail_payload = sync_run_detail_response.json()
    assert sync_run_detail_payload["id"] == "sync-latest"
    assert sync_run_detail_payload["source_snapshot_count"] == 1
    assert sync_run_detail_payload["parse_output_count"] == 1
    assert sync_run_detail_payload["match_change_count"] == 1
    assert sync_run_detail_payload["source_snapshots"][0]["source_url"] == "https://www.fifa.com/article"
    assert sync_run_detail_payload["parse_outputs"][0]["model_name"] == "qwen/qwen3.5-flash-20260224"

    assert parse_output_detail_response.status_code == 200
    parse_output_detail_payload = parse_output_detail_response.json()
    assert parse_output_detail_payload["id"] == 1
    assert parse_output_detail_payload["sync_run_id"] == "sync-latest"
    assert parse_output_detail_payload["structured_data"]["total"] == 1
