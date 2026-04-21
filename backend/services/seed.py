"""核心功能：将本地官方 fixture 赛程导入数据库作为基线数据。"""

import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from backend.models.match import Match
from backend.models.match_change import MatchChange
from backend.models.match_evaluation import MatchEvaluation
from backend.models.prediction_version import PredictionVersion
from backend.repositories.matches import MatchRepository


def seed_matches_from_fixture(
    session_factory: sessionmaker[Session],
    fixture_seed_path: str | None,
) -> None:
    if not fixture_seed_path:
        return

    fixture_path = Path(fixture_seed_path)
    if not fixture_path.exists():
        return

    with session_factory() as session:
        repository = MatchRepository(session)
        payload = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
        repository.upsert_many(payload)
        _delete_non_fixture_matches(session, payload)


def _delete_non_fixture_matches(session: Session, payload: dict) -> None:
    fixture_match_ids = {
        str(match_payload["id"])
        for match_payload in payload.get("matches", [])
        if match_payload.get("id")
    }
    if not fixture_match_ids:
        return

    stale_match_ids = list(
        session.scalars(select(Match.id).where(Match.id.not_in(sorted(fixture_match_ids)))).all()
    )
    if not stale_match_ids:
        return

    session.execute(delete(MatchChange).where(MatchChange.match_id.in_(stale_match_ids)))
    session.execute(delete(MatchEvaluation).where(MatchEvaluation.match_id.in_(stale_match_ids)))
    session.execute(delete(PredictionVersion).where(PredictionVersion.match_id.in_(stale_match_ids)))
    session.execute(delete(Match).where(Match.id.in_(stale_match_ids)))
    session.commit()
