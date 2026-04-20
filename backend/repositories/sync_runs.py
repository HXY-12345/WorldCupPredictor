"""核心功能：查询同步任务列表、详情及其关联审计摘要。"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.match_change import MatchChange
from backend.models.parse_output import ParseOutput
from backend.models.source_snapshot import SourceSnapshot
from backend.models.sync_run import SyncRun


class SyncRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_payload(self) -> dict[str, Any]:
        items = [self._serialize_summary(sync_run) for sync_run in self._list_runs()]
        return {
            "items": items,
            "total": len(items),
        }

    def get_detail_payload(self, sync_run_id: str) -> dict[str, Any] | None:
        sync_run = self.session.get(SyncRun, sync_run_id)
        if sync_run is None:
            return None

        source_snapshots = self._list_source_snapshots(sync_run_id)
        parse_outputs = self._list_parse_outputs(sync_run_id)
        return {
            **self._serialize_summary(sync_run),
            "source_snapshots": source_snapshots,
            "parse_outputs": parse_outputs,
        }

    def _list_runs(self) -> list[SyncRun]:
        statement = select(SyncRun).order_by(SyncRun.started_at.desc(), SyncRun.id.desc())
        return self.session.scalars(statement).all()

    def _serialize_summary(self, sync_run: SyncRun) -> dict[str, Any]:
        return {
            "id": sync_run.id,
            "trigger_type": sync_run.trigger_type,
            "status": sync_run.status,
            "started_at": sync_run.started_at,
            "finished_at": sync_run.finished_at,
            "source_name": sync_run.source_name,
            "error_message": sync_run.error_message,
            "source_snapshot_count": self._count_source_snapshots(sync_run.id),
            "parse_output_count": self._count_parse_outputs(sync_run.id),
            "match_change_count": self._count_match_changes(sync_run.id),
        }

    def _count_source_snapshots(self, sync_run_id: str) -> int:
        return self.session.scalar(
            select(func.count()).select_from(SourceSnapshot).where(SourceSnapshot.sync_run_id == sync_run_id)
        ) or 0

    def _count_parse_outputs(self, sync_run_id: str) -> int:
        return self.session.scalar(
            select(func.count()).select_from(ParseOutput).where(ParseOutput.sync_run_id == sync_run_id)
        ) or 0

    def _count_match_changes(self, sync_run_id: str) -> int:
        return self.session.scalar(
            select(func.count()).select_from(MatchChange).where(MatchChange.sync_run_id == sync_run_id)
        ) or 0

    def _list_source_snapshots(self, sync_run_id: str) -> list[dict[str, Any]]:
        statement = (
            select(SourceSnapshot)
            .where(SourceSnapshot.sync_run_id == sync_run_id)
            .order_by(SourceSnapshot.id.asc())
        )
        snapshots = self.session.scalars(statement).all()
        return [
            {
                "id": snapshot.id,
                "source_name": snapshot.source_name,
                "source_url": snapshot.source_url,
                "content_type": snapshot.content_type,
            }
            for snapshot in snapshots
        ]

    def _list_parse_outputs(self, sync_run_id: str) -> list[dict[str, Any]]:
        statement = (
            select(ParseOutput)
            .where(ParseOutput.sync_run_id == sync_run_id)
            .order_by(ParseOutput.id.asc())
        )
        parse_outputs = self.session.scalars(statement).all()
        return [
            {
                "id": parse_output.id,
                "model_name": parse_output.model_name,
                "parser_version": parse_output.parser_version,
                "structured_total": parse_output.structured_data.get("total"),
            }
            for parse_output in parse_outputs
        ]
