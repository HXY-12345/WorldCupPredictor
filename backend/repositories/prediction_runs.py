"""核心功能：查询与更新 prediction_runs 执行记录及其详情载荷。"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.match import Match
from backend.models.prediction_run import PredictionRun


class PredictionRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def match_exists(self, match_id: str) -> bool:
        return self.session.get(Match, match_id) is not None

    def create_running(self, match_id: str) -> PredictionRun:
        prediction_run = PredictionRun(
            id=f"predrun_{uuid4().hex}",
            match_id=match_id,
            triggered_at=datetime.now(UTC).isoformat(),
            status="running",
            document_count=0,
            used_fallback_sources=False,
            stage_trace_json={},
            is_full_live_chain=False,
            has_any_fallback=False,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def mark_status(self, prediction_run_id: str, status: str) -> PredictionRun:
        prediction_run = self._get_required(prediction_run_id)
        prediction_run.status = status
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def save_research(
        self,
        prediction_run_id: str,
        *,
        planner_model: str | None,
        search_plan_json: dict[str, Any],
        search_trace_json: dict[str, Any],
        search_documents_json: list[dict[str, Any]],
        used_fallback_sources: bool,
        stage_trace_json: dict[str, Any] | None = None,
        is_full_live_chain: bool | None = None,
        has_any_fallback: bool | None = None,
    ) -> PredictionRun:
        prediction_run = self._get_required(prediction_run_id)
        prediction_run.planner_model = planner_model
        prediction_run.search_plan_json = search_plan_json
        prediction_run.search_trace_json = search_trace_json
        prediction_run.search_documents_json = search_documents_json
        prediction_run.document_count = len(search_documents_json)
        prediction_run.used_fallback_sources = used_fallback_sources
        self._apply_chain_summary(
            prediction_run,
            stage_trace_json=stage_trace_json,
            is_full_live_chain=is_full_live_chain,
            has_any_fallback=has_any_fallback,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def save_evidence(
        self,
        prediction_run_id: str,
        *,
        synthesizer_model: str | None,
        evidence_bundle_json: dict[str, Any],
        stage_trace_json: dict[str, Any] | None = None,
        is_full_live_chain: bool | None = None,
        has_any_fallback: bool | None = None,
    ) -> PredictionRun:
        prediction_run = self._get_required(prediction_run_id)
        prediction_run.synthesizer_model = synthesizer_model
        prediction_run.evidence_bundle_json = evidence_bundle_json
        self._apply_chain_summary(
            prediction_run,
            stage_trace_json=stage_trace_json,
            is_full_live_chain=is_full_live_chain,
            has_any_fallback=has_any_fallback,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def mark_succeeded(
        self,
        prediction_run_id: str,
        *,
        prediction_version_id: int,
        decider_model: str | None,
        elapsed_ms: int,
        stage_trace_json: dict[str, Any] | None = None,
        is_full_live_chain: bool | None = None,
        has_any_fallback: bool | None = None,
    ) -> PredictionRun:
        prediction_run = self._get_required(prediction_run_id)
        prediction_run.status = "succeeded"
        prediction_run.prediction_version_id = prediction_version_id
        prediction_run.decider_model = decider_model
        prediction_run.elapsed_ms = elapsed_ms
        prediction_run.finished_at = datetime.now(UTC).isoformat()
        self._apply_chain_summary(
            prediction_run,
            stage_trace_json=stage_trace_json,
            is_full_live_chain=is_full_live_chain,
            has_any_fallback=has_any_fallback,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def mark_failed(
        self,
        prediction_run_id: str,
        *,
        error_message: str,
        elapsed_ms: int,
        stage_trace_json: dict[str, Any] | None = None,
        is_full_live_chain: bool | None = None,
        has_any_fallback: bool | None = None,
    ) -> PredictionRun:
        prediction_run = self._get_required(prediction_run_id)
        prediction_run.status = "failed"
        prediction_run.error_message = error_message
        prediction_run.elapsed_ms = elapsed_ms
        prediction_run.finished_at = datetime.now(UTC).isoformat()
        self._apply_chain_summary(
            prediction_run,
            stage_trace_json=stage_trace_json,
            is_full_live_chain=is_full_live_chain,
            has_any_fallback=has_any_fallback,
        )
        self.session.add(prediction_run)
        self.session.commit()
        return prediction_run

    def list_payload(self, match_id: str) -> dict[str, Any]:
        items = [self._serialize_summary(item) for item in self._list_runs(match_id)]
        return {
            "items": items,
            "total": len(items),
        }

    def get_detail_payload(self, prediction_run_id: str) -> dict[str, Any] | None:
        prediction_run = self.session.get(PredictionRun, prediction_run_id)
        if prediction_run is None:
            return None

        return {
            **self._serialize_summary(prediction_run),
            "stage_trace_json": prediction_run.stage_trace_json,
            "search_plan_json": prediction_run.search_plan_json,
            "search_trace_json": prediction_run.search_trace_json,
            "search_documents_json": prediction_run.search_documents_json,
            "evidence_bundle_json": prediction_run.evidence_bundle_json,
        }

    def _list_runs(self, match_id: str) -> list[PredictionRun]:
        statement = (
            select(PredictionRun)
            .where(PredictionRun.match_id == match_id)
            .order_by(PredictionRun.triggered_at.desc(), PredictionRun.id.desc())
        )
        return self.session.scalars(statement).all()

    def _get_required(self, prediction_run_id: str) -> PredictionRun:
        prediction_run = self.session.get(PredictionRun, prediction_run_id)
        if prediction_run is None:
            raise KeyError(f"Prediction run '{prediction_run_id}' was not found.")
        return prediction_run

    def _serialize_summary(self, prediction_run: PredictionRun) -> dict[str, Any]:
        return {
            "id": prediction_run.id,
            "match_id": prediction_run.match_id,
            "triggered_at": prediction_run.triggered_at,
            "finished_at": prediction_run.finished_at,
            "status": prediction_run.status,
            "prediction_version_id": prediction_run.prediction_version_id,
            "planner_model": prediction_run.planner_model,
            "synthesizer_model": prediction_run.synthesizer_model,
            "decider_model": prediction_run.decider_model,
            "elapsed_ms": prediction_run.elapsed_ms,
            "document_count": prediction_run.document_count,
            "used_fallback_sources": prediction_run.used_fallback_sources,
            "error_message": prediction_run.error_message,
            "is_full_live_chain": prediction_run.is_full_live_chain,
            "has_any_fallback": prediction_run.has_any_fallback,
        }

    def _apply_chain_summary(
        self,
        prediction_run: PredictionRun,
        *,
        stage_trace_json: dict[str, Any] | None,
        is_full_live_chain: bool | None,
        has_any_fallback: bool | None,
    ) -> None:
        if stage_trace_json is not None:
            prediction_run.stage_trace_json = dict(stage_trace_json)
        if is_full_live_chain is not None:
            prediction_run.is_full_live_chain = is_full_live_chain
        if has_any_fallback is not None:
            prediction_run.has_any_fallback = has_any_fallback
