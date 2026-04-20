"""核心功能：将本地官方 fixture 赛程导入数据库作为基线数据。"""

import json
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

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
        if repository.count() > 0:
            return

        payload = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
        repository.upsert_many(payload)
