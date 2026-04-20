"""核心功能：提供解析结果明细的查询接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.repositories.parse_outputs import ParseOutputRepository


def create_parse_outputs_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/parse-outputs/{parse_output_id}")
    def get_parse_output_detail(parse_output_id: int) -> dict:
        with session_factory() as session:
            repository = ParseOutputRepository(session)
            payload = repository.get_detail_payload(parse_output_id)
            if payload is None:
                raise HTTPException(status_code=404, detail=f"Parse output '{parse_output_id}' was not found.")
            return payload

    return router
