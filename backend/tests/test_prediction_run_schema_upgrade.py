"""核心功能：验证旧版 prediction_runs 表在现有 sqlite 数据库上会被自动补齐新列。"""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from uuid import uuid4

from sqlalchemy import text

from backend.database.session import create_session_factory, init_database
from backend.models.prediction_run import PredictionRun


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_init_database_upgrades_existing_prediction_runs_table_for_new_chain_columns():
    runtime_dir = _runtime_dir("prediction_run_schema_upgrade")
    database_path = runtime_dir / "prediction_run_schema_upgrade.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE prediction_runs (
                id VARCHAR(64) PRIMARY KEY,
                match_id VARCHAR(64),
                triggered_at VARCHAR(64),
                finished_at VARCHAR(64),
                status VARCHAR(32),
                prediction_version_id INTEGER,
                planner_model VARCHAR(128),
                synthesizer_model VARCHAR(128),
                decider_model VARCHAR(128),
                elapsed_ms INTEGER,
                document_count INTEGER DEFAULT 0,
                used_fallback_sources BOOLEAN DEFAULT 0,
                error_message VARCHAR(512),
                search_plan_json JSON,
                search_trace_json JSON,
                search_documents_json JSON,
                evidence_bundle_json JSON
            )
            """
        )
        connection.commit()

    engine, session_factory = create_session_factory(f"sqlite:///{database_path}")
    init_database(engine)

    with engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(prediction_runs)"))
        }

    assert "stage_trace_json" in columns
    assert "is_full_live_chain" in columns
    assert "has_any_fallback" in columns

    with session_factory() as session:
        session.add(
            PredictionRun(
                id="predrun_upgrade_test",
                match_id="fwc2026-m001",
                triggered_at=datetime.now(UTC).isoformat(),
                status="succeeded",
                finished_at=datetime.now(UTC).isoformat(),
                prediction_version_id=None,
                planner_model="fallback-research-v1",
                synthesizer_model="fallback-evidence-v1",
                decider_model="static-test-model",
                elapsed_ms=1234,
                document_count=5,
                used_fallback_sources=True,
                error_message=None,
                stage_trace_json={
                    "research": {
                        "mode": "fallback",
                        "model_name": "fallback-research-v1",
                        "elapsed_ms": 10,
                        "error_message": "Live research stage is not configured.",
                    }
                },
                is_full_live_chain=False,
                has_any_fallback=True,
                search_plan_json={"match_id": "fwc2026-m001", "queries": []},
                search_trace_json={"completed": True},
                search_documents_json=[],
                evidence_bundle_json={"match_id": "fwc2026-m001"},
            )
        )
        session.commit()
