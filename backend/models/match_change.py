"""核心功能：定义比赛字段变更历史表的 ORM 结构。"""

from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class MatchChange(Base):
    __tablename__ = "match_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), index=True)
    sync_run_id: Mapped[str] = mapped_column(ForeignKey("sync_runs.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(64))
    old_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    change_type: Mapped[str] = mapped_column(String(32))
    changed_at: Mapped[str] = mapped_column(String(64))
