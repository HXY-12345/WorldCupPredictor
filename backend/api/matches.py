"""核心功能：提供比赛列表、比赛变更历史等只读查询接口。"""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.repositories.match_changes import MatchChangeRepository
from backend.repositories.matches import MatchRepository


def create_matches_router(session_factory: Callable[[], Session]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/matches")
    def list_matches() -> dict:
        with session_factory() as session:
            repository = MatchRepository(session)
            return repository.list_payload()

    @router.get("/api/matches/{match_id}/changes")
    def list_match_changes(match_id: str) -> dict:
        with session_factory() as session:
            repository = MatchChangeRepository(session)
            if not repository.match_exists(match_id):
                raise HTTPException(status_code=404, detail=f"Match '{match_id}' was not found.")
            return repository.list_payload(match_id)

    return router
