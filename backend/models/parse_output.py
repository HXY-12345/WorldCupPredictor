"""核心功能：定义解析结果审计表的 ORM 结构。"""

from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class ParseOutput(Base):
    __tablename__ = "parse_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_run_id: Mapped[str] = mapped_column(ForeignKey("sync_runs.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(128))
    parser_version: Mapped[str] = mapped_column(String(64))
    structured_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
