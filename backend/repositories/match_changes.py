"""核心功能：查询单场比赛的字段变更历史时间线。"""

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.match import Match
from backend.models.match_change import MatchChange


class MatchChangeRepository:
    def __init__(self, session: Session):
        self.session = session

    def match_exists(self, match_id: str) -> bool:
        return self.session.get(Match, match_id) is not None

    def list_payload(self, match_id: str) -> dict[str, Any]:
        items = [self._serialize(change) for change in self._list_changes(match_id)]
        return {
            "match_id": match_id,
            "items": items,
            "total": len(items),
        }

    def _list_changes(self, match_id: str) -> Iterable[MatchChange]:
        statement = (
            select(MatchChange)
            .where(MatchChange.match_id == match_id)
            .order_by(MatchChange.changed_at.asc(), MatchChange.id.asc())
        )
        return self.session.scalars(statement).all()

    def _serialize(self, change: MatchChange) -> dict[str, Any]:
        return {
            "id": change.id,
            "match_id": change.match_id,
            "sync_run_id": change.sync_run_id,
            "field_name": change.field_name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "change_type": change.change_type,
            "changed_at": change.changed_at,
        }
