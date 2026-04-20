"""核心功能：定义比赛当前事实表的 ORM 结构。"""

from typing import Any

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    official_match_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kickoff_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[str] = mapped_column(String(32), index=True)
    time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(128), nullable=True)
    home_team: Mapped[dict[str, Any]] = mapped_column(JSON)
    away_team: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    prediction: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    head_to_head: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    key_players: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_updated_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
