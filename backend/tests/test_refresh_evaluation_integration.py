"""核心功能：验证 refresh 在比赛完赛后会自动写入或修正评估结果。"""

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from backend.database.session import create_session_factory, init_database
from backend.models.match_evaluation import MatchEvaluation
from backend.models.prediction_version import PredictionVersion
from backend.services.refresh import FetchedSource, RefreshPipeline, run_refresh


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
                        "date": "2026-06-12",
                        "time": "03:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                        "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
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


def _prediction_payload(home: int, away: int, predicted_at: str) -> dict:
    return {
        "predicted_score": {"home": home, "away": away},
        "outcome_pick": "home_win" if home > away else "draw" if home == away else "away_win",
        "home_goals_pick": home,
        "away_goals_pick": away,
        "total_goals_pick": home + away,
        "confidence": 75,
        "reasoning_summary": "Refresh integration prediction.",
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
            "date": "2026-06-12",
            "time": "03:00",
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
class StaticParser:
    payload: dict

    def parse(self, sources: list[FetchedSource], context) -> dict:
        return {
            "model_name": "openrouter/auto",
            "parser_version": "openrouter-v1",
            "structured_data": self.payload,
        }


def test_refresh_auto_evaluates_finished_matches_and_updates_existing_evaluation():
    runtime_dir = _runtime_dir("refresh_evaluation")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "refresh_evaluation.db"
    engine, session_factory = create_session_factory(f"sqlite:///{database_path}")
    init_database(engine)

    with session_factory() as session:
        session.add(
            PredictionVersion(
                match_id="fwc2026-m001",
                version_no=1,
                created_at="2026-06-11T17:30:00Z",
                model_name="static-test-model",
                prediction=_prediction_payload(2, 1, "2026-06-11T17:30:00Z"),
            )
        )
        session.commit()

    first_pipeline = RefreshPipeline(
        fetcher=FakeFetcher(),
        parser=StaticParser(
            {
                "matches": [
                    {
                        "id": "fwc2026-m001",
                        "official_match_number": 1,
                        "kickoff_label": "M001",
                        "sort_order": 1,
                        "date": "2026-06-12",
                        "time": "03:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                        "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
                        "status": "finished",
                        "score": {"home": 2, "away": 1},
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-06-11T22:00:00Z",
                "total": 1,
            }
        ),
    )
    second_pipeline = RefreshPipeline(
        fetcher=FakeFetcher(),
        parser=StaticParser(
            {
                "matches": [
                    {
                        "id": "fwc2026-m001",
                        "official_match_number": 1,
                        "kickoff_label": "M001",
                        "sort_order": 1,
                        "date": "2026-06-12",
                        "time": "03:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {"name": "Mexico", "flag": "MX", "fifa_rank": None, "form": []},
                        "away_team": {"name": "South Africa", "flag": "ZA", "fifa_rank": None, "form": []},
                        "status": "finished",
                        "score": {"home": 1, "away": 1},
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-06-11T23:00:00Z",
                "total": 1,
            }
        ),
    )

    run_refresh(session_factory, str(fixture_path), refresh_pipeline=first_pipeline)
    run_refresh(session_factory, str(fixture_path), refresh_pipeline=second_pipeline)

    with session_factory() as session:
        evaluation = session.scalar(select(MatchEvaluation).where(MatchEvaluation.match_id == "fwc2026-m001"))

    assert evaluation is not None
    assert evaluation.evaluation_status == "scored"
    assert evaluation.actual_home_score == 1
    assert evaluation.actual_away_score == 1
    assert evaluation.exact_score_hit is False
    assert evaluation.grade == "partial_hit"
