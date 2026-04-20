"""核心功能：定义比赛预测历史版本表的 ORM 结构。"""

from typing import Any

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class PredictionVersion(Base):
    __tablename__ = "prediction_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prediction: Mapped[dict[str, Any]] = mapped_column(JSON)
