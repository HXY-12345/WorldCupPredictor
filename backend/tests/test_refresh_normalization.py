"""核心功能：验证真实模型的非规范增量输出会先被标准化再入库。"""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from backend.core.config import Settings
from backend.database.session import create_session_factory, init_database
from backend.models.match import Match
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
class NonCanonicalIncrementalParser:
    def parse(self, sources: list[FetchedSource], context) -> dict:
        assert context.mode == "incremental"
        return {
            "model_name": "openrouter/auto",
            "parser_version": "openrouter-v1",
            "structured_data": {
                "matches": [
                    {
                        "match_id": "fwc2026-m001",
                        "date": "2026-06-11",
                        "time": "13:00",
                        "timezone": "America/Mexico_City",
                        "venue": "Mexico City Stadium",
                        "home_team": "Mexico",
                        "away_team": "South Africa",
                        "group": "Group A",
                        "status": "finished",
                        "score": {"home": 2, "away": 1},
                        "prediction": None,
                    }
                ],
                "last_updated": "2026-06-11T22:00:00Z",
                "total": 1,
            },
        }


def test_incremental_refresh_normalizes_realistic_model_payload_before_upsert():
    runtime_dir = _runtime_dir("refresh_normalization")
    database_path = runtime_dir / "refresh_normalization.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
    )
    engine, session_factory = create_session_factory(settings.database_url)
    init_database(engine)

    with session_factory() as session:
        session.add(
            Match(
                id="fwc2026-m001",
                official_match_number=1,
                kickoff_label="M001",
                sort_order=1,
                date="2026-06-11",
                time="TBD",
                stage="Group Stage",
                group_name="A",
                venue="Mexico City Stadium",
                home_team={"name": "Mexico", "flag": "MX", "fifa_rank": 14, "form": []},
                away_team={"name": "South Africa", "flag": "ZA", "fifa_rank": 54, "form": []},
                status="not_started",
                score=None,
                prediction={"home_score": 1, "away_score": 0},
                head_to_head=None,
                key_players={"home_injured": [], "away_suspended": []},
                source_updated_at="2026-03-31T00:00:00Z",
            )
        )
        session.commit()

    pipeline = RefreshPipeline(fetcher=FakeFetcher(), parser=NonCanonicalIncrementalParser())

    sync_run = run_refresh(
        session_factory=session_factory,
        refresh_pipeline=pipeline,
        fixture_seed_path=None,
    )

    with session_factory() as session:
        match = session.get(Match, "fwc2026-m001")

    assert sync_run.status == "completed"
    assert match.group_name == "A"
    assert match.date == "2026-06-12"
    assert match.time == "03:00"
    assert match.home_team["name"] == "Mexico"
    assert match.away_team["name"] == "South Africa"
    assert match.status == "finished"
    assert match.score == {"home": 2, "away": 1}
    assert match.prediction == {"home_score": 1, "away_score": 0}
