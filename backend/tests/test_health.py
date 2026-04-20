"""核心功能：验证健康检查接口能够稳定返回可用状态。"""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.main import create_app


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_health_endpoint_returns_ok():
    runtime_dir = _runtime_dir("health")
    database_path = runtime_dir / "health.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=False,
        fixture_seed_path=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
