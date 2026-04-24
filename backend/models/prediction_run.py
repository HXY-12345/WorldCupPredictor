"""核心功能：定义单次预测执行记录表的 ORM 结构。"""

from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class PredictionRun(Base):
    __tablename__ = "prediction_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    match_id: Mapped[str] = mapped_column(String(64), index=True)
    triggered_at: Mapped[str] = mapped_column(String(64), index=True)
    finished_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    prediction_version_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("prediction_versions.id"),
        nullable=True,
        index=True,
    )
    planner_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    synthesizer_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decider_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    used_fallback_sources: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stage_trace_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_full_live_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    has_any_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    search_plan_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    search_trace_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    search_documents_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_bundle_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
