"""核心功能：封装比赛事实表的查询、增量合并与变更审计写入。"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from collections.abc import Iterable
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.match import Match
from backend.models.match_change import MatchChange

PLACEHOLDER_TEAM_MARKERS = (
    "winner ",
    "runner-up",
    "runner up",
    "loser ",
    "match ",
    "tbd",
)
PLACEHOLDER_TEXT_MARKERS = ("tbd", "tbc", "unknown")
STATUS_RANK = {
    "scheduled": 1,
    "not_started": 1,
    "in_progress": 2,
    "live": 2,
    "finished": 3,
    "completed": 3,
}


@dataclass(frozen=True)
class UpdateDecision:
    should_update: bool
    new_value: Any
    change_type: str | None = None


class MatchRepository:
    def __init__(self, session: Session):
        self.session = session

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Match)) or 0

    def upsert_many(self, payload: dict[str, Any], sync_run_id: str | None = None) -> None:
        last_updated = payload.get("last_updated") or payload.get("lastUpdated")

        for match_payload in payload.get("matches", []):
            self._upsert_match(match_payload, last_updated, sync_run_id)

        self.session.commit()

    def list_payload(self) -> dict[str, Any]:
        matches = list(self._list_matches())
        last_updated = self.session.scalar(select(func.max(Match.source_updated_at)))
        return {
            "matches": [self._serialize(match) for match in matches],
            "last_updated": last_updated,
            "total": len(matches),
        }

    def _list_matches(self) -> Iterable[Match]:
        statement = select(Match).order_by(Match.date.asc(), Match.sort_order.asc(), Match.id.asc())
        return self.session.scalars(statement).all()

    def _upsert_match(
        self,
        match_payload: dict[str, Any],
        last_updated: str | None,
        sync_run_id: str | None,
    ) -> None:
        match = self.session.get(Match, match_payload["id"])
        if match is None:
            match = Match(id=match_payload["id"])
            self._apply_initial_payload(match, match_payload, last_updated)
        else:
            self._apply_incremental_payload(match, match_payload, last_updated, sync_run_id)

        self.session.add(match)

    def _apply_initial_payload(self, match: Match, match_payload: dict[str, Any], last_updated: str | None) -> None:
        match.official_match_number = match_payload.get("official_match_number")
        match.kickoff_label = match_payload.get("kickoff_label")
        match.sort_order = match_payload.get("sort_order") or 0
        match.date = match_payload["date"]
        match.time = match_payload.get("time")
        match.stage = match_payload.get("stage")
        match.group_name = match_payload.get("group")
        match.venue = match_payload.get("venue")
        match.home_team = deepcopy(match_payload.get("home_team") or {})
        match.away_team = deepcopy(match_payload.get("away_team") or {})
        match.status = match_payload.get("status")
        match.score = deepcopy(match_payload.get("score"))
        match.prediction = deepcopy(match_payload.get("prediction"))
        match.head_to_head = deepcopy(match_payload.get("head_to_head"))
        match.key_players = deepcopy(match_payload.get("key_players"))
        match.source_updated_at = last_updated

    def _apply_incremental_payload(
        self,
        match: Match,
        match_payload: dict[str, Any],
        last_updated: str | None,
        sync_run_id: str | None,
    ) -> None:
        field_mappings = [
            ("official_match_number", "official_match_number", "baseline"),
            ("kickoff_label", "kickoff_label", "baseline"),
            ("sort_order", "sort_order", "baseline"),
            ("date", "date", "baseline"),
            ("time", "time", "baseline"),
            ("stage", "stage", "baseline"),
            ("group", "group_name", "baseline"),
            ("venue", "venue", "baseline"),
            ("home_team", "home_team", "team"),
            ("away_team", "away_team", "team"),
            ("status", "status", "status"),
            ("score", "score", "score"),
            ("head_to_head", "head_to_head", "json"),
            ("key_players", "key_players", "json"),
        ]
        changed_at = last_updated or datetime.now(UTC).isoformat()

        for payload_key, attribute_name, strategy in field_mappings:
            current_value = getattr(match, attribute_name)
            incoming_value = match_payload.get(payload_key)
            decision = self._resolve_update_decision(strategy, current_value, incoming_value)

            if not decision.should_update:
                continue

            if sync_run_id:
                self.session.add(
                    MatchChange(
                        match_id=match.id,
                        sync_run_id=sync_run_id,
                        field_name=payload_key,
                        old_value=deepcopy(current_value),
                        new_value=deepcopy(decision.new_value),
                        change_type=decision.change_type or "corrected",
                        changed_at=changed_at,
                    )
                )

            setattr(match, attribute_name, deepcopy(decision.new_value))

        if not match.prediction and self._has_meaningful_value(match_payload.get("prediction")):
            match.prediction = deepcopy(match_payload.get("prediction"))
        if not match.source_updated_at or last_updated:
            match.source_updated_at = last_updated or match.source_updated_at

    def _resolve_update_decision(
        self,
        strategy: str,
        current_value: Any,
        incoming_value: Any,
    ) -> UpdateDecision:
        if strategy == "baseline":
            return self._resolve_baseline_update(current_value, incoming_value)
        if strategy == "team":
            return self._resolve_team_update(current_value, incoming_value)
        if strategy == "status":
            return self._resolve_status_update(current_value, incoming_value)
        if strategy == "score":
            return self._resolve_score_update(current_value, incoming_value)
        return self._resolve_json_update(current_value, incoming_value)

    def _resolve_baseline_update(self, current_value: Any, incoming_value: Any) -> UpdateDecision:
        if not self._has_meaningful_value(incoming_value) or current_value == incoming_value:
            return UpdateDecision(False, current_value)
        if not self._has_meaningful_value(current_value):
            return UpdateDecision(True, incoming_value, "filled")
        if self._is_placeholder_text(incoming_value) and not self._is_placeholder_text(current_value):
            return UpdateDecision(False, current_value)
        if self._is_placeholder_text(current_value) and not self._is_placeholder_text(incoming_value):
            return UpdateDecision(True, incoming_value, "filled")
        return UpdateDecision(True, incoming_value, "corrected")

    def _resolve_team_update(self, current_value: Any, incoming_value: Any) -> UpdateDecision:
        if not self._has_meaningful_value(incoming_value) or current_value == incoming_value:
            return UpdateDecision(False, current_value)
        if not self._has_meaningful_value(current_value):
            return UpdateDecision(True, incoming_value, "filled")

        current_is_placeholder = self._is_placeholder_team(current_value)
        incoming_is_placeholder = self._is_placeholder_team(incoming_value)

        if current_is_placeholder and not incoming_is_placeholder:
            return UpdateDecision(True, incoming_value, "filled")
        if not current_is_placeholder and incoming_is_placeholder:
            return UpdateDecision(False, current_value)
        return UpdateDecision(True, incoming_value, "corrected")

    def _resolve_status_update(self, current_value: Any, incoming_value: Any) -> UpdateDecision:
        if not self._has_meaningful_value(incoming_value) or current_value == incoming_value:
            return UpdateDecision(False, current_value)

        current_rank = STATUS_RANK.get(str(current_value).lower()) if current_value else None
        incoming_rank = STATUS_RANK.get(str(incoming_value).lower()) if incoming_value else None
        if current_rank is not None and incoming_rank is not None and incoming_rank < current_rank:
            return UpdateDecision(False, current_value)

        return UpdateDecision(True, incoming_value, "result_updated")

    def _resolve_score_update(self, current_value: Any, incoming_value: Any) -> UpdateDecision:
        if not self._has_meaningful_value(incoming_value) or current_value == incoming_value:
            return UpdateDecision(False, current_value)
        return UpdateDecision(True, incoming_value, "result_updated")

    def _resolve_json_update(self, current_value: Any, incoming_value: Any) -> UpdateDecision:
        if not self._has_meaningful_value(incoming_value) or current_value == incoming_value:
            return UpdateDecision(False, current_value)
        if not self._has_meaningful_value(current_value):
            return UpdateDecision(True, incoming_value, "filled")
        return UpdateDecision(True, incoming_value, "corrected")

    def _has_meaningful_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, dict):
            return bool(value)
        if isinstance(value, list):
            return bool(value)
        return True

    def _is_placeholder_team(self, team_payload: Any) -> bool:
        if not isinstance(team_payload, dict):
            return False
        team_name = str(team_payload.get("name") or "").strip().lower()
        if not team_name:
            return False
        return any(marker in team_name for marker in PLACEHOLDER_TEAM_MARKERS)

    def _is_placeholder_text(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        normalized = value.strip().lower()
        if not normalized:
            return False
        return any(marker in normalized for marker in PLACEHOLDER_TEXT_MARKERS)

    def _serialize(self, match: Match) -> dict[str, Any]:
        return {
            "id": match.id,
            "official_match_number": match.official_match_number,
            "kickoff_label": match.kickoff_label,
            "sort_order": match.sort_order,
            "date": match.date,
            "time": match.time,
            "stage": match.stage,
            "group": match.group_name,
            "venue": match.venue,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "status": match.status,
            "score": match.score,
            "prediction": match.prediction,
            "head_to_head": match.head_to_head,
            "key_players": match.key_players,
        }
