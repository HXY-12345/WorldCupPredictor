"""核心功能：验证增量 refresh 的字段更新、审计与非回退规则。"""

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from backend.core.config import Settings
from backend.database.session import create_session_factory, init_database
from backend.models.match import Match
from backend.models.match_change import MatchChange
from backend.services.refresh import FetchedSource, RefreshPipeline, run_refresh


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


@dataclass
class FakeFetcher:
    def fetch(self) -> list[FetchedSource]:
        return [
            FetchedSource(
                source_name="fifa_article",
                source_url="https://www.fifa.com/article",
                content_type="text/html",
                raw_body="<html><body>Official FIFA schedule source</body></html>",
                extracted_text="Official FIFA schedule source",
            )
        ]


@dataclass
class SequenceParser:
    payloads: list[dict]
    index: int = field(default=0, init=False)

    def parse(self, sources: list[FetchedSource]) -> dict:
        payload = self.payloads[self.index]
        self.index += 1
        return {
            "model_name": "openrouter/auto",
            "parser_version": "openrouter-v1",
            "structured_data": payload,
        }


def _match_payload() -> dict:
    return {
        "matches": [
            {
                "id": "fwc2026-r32-001",
                "official_match_number": 73,
                "kickoff_label": "M073",
                "sort_order": 73,
                "date": "2026-06-28",
                "time": "TBD",
                "stage": "Round of 32",
                "group": None,
                "venue": "TBD Stadium",
                "home_team": {
                    "name": "Winner Group A",
                    "flag": None,
                    "fifa_rank": None,
                    "form": [],
                },
                "away_team": {
                    "name": "Runner-up Group B",
                    "flag": None,
                    "fifa_rank": None,
                    "form": [],
                },
                "status": "not_started",
                "score": None,
                "prediction": None,
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


def test_incremental_refresh_updates_latest_facts_and_records_match_change_history():
    runtime_dir = _runtime_dir("incremental_refresh")
    database_path = runtime_dir / "incremental_refresh.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
    )
    engine, session_factory = create_session_factory(settings.database_url)
    init_database(engine)

    initial_payload = _match_payload()

    updated_payload = deepcopy(initial_payload)
    updated_match = updated_payload["matches"][0]
    updated_match["time"] = "20:00"
    updated_match["venue"] = "Dallas Stadium"
    updated_match["home_team"] = {
        "name": "Mexico",
        "flag": "MX",
        "fifa_rank": 14,
        "form": ["W", "D", "W"],
    }
    updated_match["away_team"] = {
        "name": "Japan",
        "flag": "JP",
        "fifa_rank": 18,
        "form": ["W", "W", "L"],
    }
    updated_match["status"] = "finished"
    updated_match["score"] = {
        "home": 2,
        "away": 1,
    }
    updated_payload["last_updated"] = "2026-06-28T22:00:00Z"

    regressed_payload = deepcopy(initial_payload)
    regressed_payload["last_updated"] = "2026-06-28T23:00:00Z"

    pipeline = RefreshPipeline(
        fetcher=FakeFetcher(),
        parser=SequenceParser([initial_payload, updated_payload, regressed_payload]),
    )

    first_sync_run = run_refresh(
        session_factory=session_factory,
        refresh_pipeline=pipeline,
        fixture_seed_path=None,
    )

    with session_factory() as session:
        match = session.get(Match, "fwc2026-r32-001")
        match.prediction = {
            "home_score": 1,
            "away_score": 0,
            "confidence": 71,
            "reasoning": "Manual pre-match prediction",
            "predicted_at": "2026-06-20T00:00:00Z",
        }
        session.add(match)
        session.commit()

    second_sync_run = run_refresh(
        session_factory=session_factory,
        refresh_pipeline=pipeline,
        fixture_seed_path=None,
    )
    third_sync_run = run_refresh(
        session_factory=session_factory,
        refresh_pipeline=pipeline,
        fixture_seed_path=None,
    )

    with session_factory() as session:
        match = session.get(Match, "fwc2026-r32-001")
        changes = session.scalars(select(MatchChange).order_by(MatchChange.id.asc())).all()

    assert first_sync_run.status == "completed"
    assert second_sync_run.status == "completed"
    assert third_sync_run.status == "completed"

    assert match.time == "20:00"
    assert match.venue == "Dallas Stadium"
    assert match.home_team["name"] == "Mexico"
    assert match.away_team["name"] == "Japan"
    assert match.status == "finished"
    assert match.score == {"home": 2, "away": 1}
    assert match.prediction["confidence"] == 71

    assert len(changes) == 6
    assert {change.sync_run_id for change in changes} == {second_sync_run.id}
    assert {change.field_name: change.change_type for change in changes} == {
        "time": "filled",
        "venue": "filled",
        "home_team": "filled",
        "away_team": "filled",
        "status": "result_updated",
        "score": "result_updated",
    }
