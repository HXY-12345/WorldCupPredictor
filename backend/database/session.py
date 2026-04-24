"""核心功能：创建数据库引擎、会话工厂，并在初始化时兼容升级 SQLite 旧表结构。"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.base import Base


def _ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)

    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return

    Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    _ensure_sqlite_directory(database_url)

    engine_kwargs: dict = {"future": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_kwargs)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return engine, session_factory


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    _upgrade_sqlite_prediction_runs_table(engine)


def _upgrade_sqlite_prediction_runs_table(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        if not _sqlite_table_exists(connection, "prediction_runs"):
            return

        existing_columns = _sqlite_table_columns(connection, "prediction_runs")
        required_columns = {
            "stage_trace_json": "stage_trace_json JSON",
            "is_full_live_chain": "is_full_live_chain BOOLEAN NOT NULL DEFAULT 0",
            "has_any_fallback": "has_any_fallback BOOLEAN NOT NULL DEFAULT 0",
        }

        for column_name, column_sql in required_columns.items():
            if column_name in existing_columns:
                continue
            connection.exec_driver_sql(f"ALTER TABLE prediction_runs ADD COLUMN {column_sql}")


def _sqlite_table_exists(connection: Connection, table_name: str) -> bool:
    result = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return result.first() is not None


def _sqlite_table_columns(connection: Connection, table_name: str) -> set[str]:
    result = connection.exec_driver_sql(f"PRAGMA table_info({table_name})")
    return {row[1] for row in result}
