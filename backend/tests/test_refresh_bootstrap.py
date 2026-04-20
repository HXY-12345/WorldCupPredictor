"""核心功能：验证首刷先建完整基线再叠加实时更新的行为。"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from backend.core.config import Settings
from backend.database.session import create_session_factory, init_database
from backend.repositories.matches import MatchRepository
from backend.services.refresh import FetchedSource, RefreshPipeline, run_refresh


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_baseline_fixture(path: Path) -> None:
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
                            "fifa_rank": None,
                            "form": [],
                        },
                        "away_team": {
                            "name": "TBD",
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
                    },
                    {
                        "id": "fwc2026-m002",
                        "official_match_number": 2,
                        "kickoff_label": "M002",
                        "sort_order": 2,
                        "date": "2026-06-12",
                        "time": "20:00",
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
                        "prediction": None,
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
class ContextAwareParser:
    payload: dict
    seen_modes: list[str] = field(default_factory=list)

    def parse(self, sources: list[FetchedSource], context) -> dict:
        self.seen_modes.append(context.mode)
        return {
            "model_name": "openrouter/auto",
            "parser_version": "openrouter-v1",
            "structured_data": self.payload,
        }


def test_first_refresh_bootstraps_fixture_baseline_before_overlaying_live_updates():
    runtime_dir = _runtime_dir("refresh_bootstrap")
    fixture_path = runtime_dir / "baseline_fixture.json"
    _write_baseline_fixture(fixture_path)

    database_path = runtime_dir / "refresh_bootstrap.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=str(fixture_path),
    )
    engine, session_factory = create_session_factory(settings.database_url)
    init_database(engine)

    parser = ContextAwareParser(
        payload={
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
                        "fifa_rank": None,
                        "form": [],
                    },
                    "away_team": {
                        "name": "South Africa",
                        "flag": "ZA",
                        "fifa_rank": None,
                        "form": [],
                    },
                    "status": "finished",
                    "score": {
                        "home": 2,
                        "away": 1,
                    },
                    "prediction": None,
                    "head_to_head": None,
                    "key_players": {
                        "home_injured": [],
                        "away_suspended": [],
                    },
                }
            ],
            "last_updated": "2026-06-11T22:00:00Z",
            "total": 1,
        }
    )
    pipeline = RefreshPipeline(fetcher=FakeFetcher(), parser=parser)

    first_sync_run = run_refresh(
        session_factory=session_factory,
        fixture_seed_path=str(fixture_path),
        refresh_pipeline=pipeline,
    )
    second_sync_run = run_refresh(
        session_factory=session_factory,
        fixture_seed_path=str(fixture_path),
        refresh_pipeline=pipeline,
    )

    with session_factory() as session:
        repository = MatchRepository(session)
        payload = repository.list_payload()
        first_match = next(match for match in payload["matches"] if match["id"] == "fwc2026-m001")
        second_match = next(match for match in payload["matches"] if match["id"] == "fwc2026-m002")

    assert first_sync_run.status == "completed"
    assert second_sync_run.status == "completed"
    assert payload["total"] == 2
    assert first_match["away_team"]["name"] == "South Africa"
    assert first_match["score"] == {"home": 2, "away": 1}
    assert second_match["home_team"]["name"] == "Canada"
    assert parser.seen_modes == ["baseline", "incremental"]
