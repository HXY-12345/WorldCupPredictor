"""核心功能：查询解析结果明细，供详情接口直接返回。"""

from typing import Any

from sqlalchemy.orm import Session

from backend.models.parse_output import ParseOutput


class ParseOutputRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_detail_payload(self, parse_output_id: int) -> dict[str, Any] | None:
        parse_output = self.session.get(ParseOutput, parse_output_id)
        if parse_output is None:
            return None

        return {
            "id": parse_output.id,
            "sync_run_id": parse_output.sync_run_id,
            "model_name": parse_output.model_name,
            "parser_version": parse_output.parser_version,
            "structured_data": parse_output.structured_data,
            "raw_response": parse_output.raw_response,
        }
