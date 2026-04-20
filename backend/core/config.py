"""核心功能：定义应用默认配置、环境变量配置与项目路径常量。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "data" / "worldcup.db"
DEFAULT_FIXTURE_PATH = PROJECT_ROOT / "backend" / "data" / "fixtures" / "official_schedule.json"
DEFAULT_OPENROUTER_MODEL_CONFIG_PATH = PROJECT_ROOT / "backend" / "config" / "openrouter.model.json"
DEFAULT_OPENROUTER_KEY_PATH = PROJECT_ROOT / "backend" / "config" / "openrouter.key"
DEFAULT_PREDICTION_OPENROUTER_MODEL_CONFIG_PATH = (
    PROJECT_ROOT / "backend" / "config" / "openrouter.prediction.model.json"
)
DEFAULT_PREDICTION_OPENROUTER_KEY_PATH = PROJECT_ROOT / "backend" / "config" / "openrouter.prediction.key"
DEFAULT_FIFA_ARTICLE_URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/"
    "articles/match-schedule-fixtures-results-teams-stadiums"
)
DEFAULT_FIFA_SCHEDULE_PDF_URL = (
    "https://fwc26teambasecamps.fifa.com/ReactApps/TBC/dist/static/media/"
    "match-schedule-english.071cf28145379e10f0cf.pdf"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WORLDCUP_",
        extra="ignore",
    )

    app_name: str = "WorldCup Predictor API"
    database_url: str = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
    enable_fixture_seed: bool = True
    fixture_seed_path: str | None = str(DEFAULT_FIXTURE_PATH)
    openrouter_model_config_path: str | None = str(DEFAULT_OPENROUTER_MODEL_CONFIG_PATH)
    openrouter_key_path: str | None = str(DEFAULT_OPENROUTER_KEY_PATH)
    fifa_article_url: str = DEFAULT_FIFA_ARTICLE_URL
    fifa_schedule_pdf_url: str = DEFAULT_FIFA_SCHEDULE_PDF_URL
    refresh_request_timeout_seconds: float = 120.0
    prediction_openrouter_model_config_path: str | None = str(DEFAULT_PREDICTION_OPENROUTER_MODEL_CONFIG_PATH)
    prediction_openrouter_key_path: str | None = str(DEFAULT_PREDICTION_OPENROUTER_KEY_PATH)
    prediction_request_timeout_seconds: float = 90.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
