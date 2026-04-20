"""核心功能：验证 refresh 流水线会写入快照、解析结果并 upsert 比赛。"""

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from backend.core.config import Settings
from backend.database.session import create_session_factory, init_database
from backend.models.parse_output import ParseOutput
from backend.models.source_snapshot import SourceSnapshot
from backend.repositories.matches import MatchRepository
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
                extracted_text="Official FIFA schedule source"
            )
        ]


@dataclass
class FakeParser:
    def parse(self, sources: list[FetchedSource]) -> dict:
        assert len(sources) == 1
        return {
            "model_name": "openrouter/auto",
            "parser_version": "openrouter-v1",
            "structured_data": {
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
                            "form": []
                        },
                        "away_team": {
                            "name": "South Africa",
                            "flag": "ZA",
                            "fifa_rank": None,
                            "form": []
                        },
                        "status": "not_started",
                        "score": None,
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": {
                            "home_injured": [],
                            "away_suspended": []
                        }
                    }
                ],
                "last_updated": "2026-03-31T00:00:00Z",
                "total": 1
            }
        }


def test_run_refresh_records_snapshots_parse_outputs_and_upserts_matches():
    runtime_dir = _runtime_dir("refresh_pipeline")
    database_path = runtime_dir / "pipeline.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
    )
    engine, session_factory = create_session_factory(settings.database_url)
    init_database(engine)

    pipeline = RefreshPipeline(
        fetcher=FakeFetcher(),
        parser=FakeParser(),
    )

    sync_run = run_refresh(
        session_factory=session_factory,
        refresh_pipeline=pipeline,
        fixture_seed_path=None,
    )

    assert sync_run.status == "completed"
    assert sync_run.source_name == "fifa_article"

    with session_factory() as session:
        repository = MatchRepository(session)
        payload = repository.list_payload()
        snapshots = session.scalars(select(SourceSnapshot)).all()
        parse_outputs = session.scalars(select(ParseOutput)).all()

    assert payload["total"] == 1
    assert payload["matches"][0]["id"] == "fwc2026-m001"
    assert len(snapshots) == 1
    assert snapshots[0].source_url == "https://www.fifa.com/article"
    assert len(parse_outputs) == 1
    assert parse_outputs[0].model_name == "openrouter/auto"
