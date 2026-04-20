"""核心功能：验证默认 fixture 可以正确导入比赛基线数据。"""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_default_fixture_seed_populates_official_schedule():
    runtime_dir = _runtime_dir("default_seed")
    database_path = runtime_dir / "worldcup.db"
    settings = Settings(database_url=f"sqlite:///{database_path}")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/matches")

    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] >= 100
    assert payload["matches"][0]["id"].startswith("fwc2026-m")
    assert payload["last_updated"] == "2026-03-31T00:00:00Z"
