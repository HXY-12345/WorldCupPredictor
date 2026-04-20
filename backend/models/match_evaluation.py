"""核心功能：定义单场比赛赛后评估结果表的 ORM 结构。"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class MatchEvaluation(Base):
    __tablename__ = "match_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prediction_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    evaluation_status: Mapped[str] = mapped_column(String(32), index=True)
    actual_home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    exact_score_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    home_goals_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    away_goals_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_goals_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rule_version: Mapped[str] = mapped_column(String(32))
    evaluated_at: Mapped[str] = mapped_column(String(64))
