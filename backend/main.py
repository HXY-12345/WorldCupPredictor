"""核心功能：组装 FastAPI 应用、数据库与各类后端路由。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import backend.models  # noqa: F401
from backend.api.analytics import create_analytics_router
from backend.api.evaluations import create_evaluations_router
from backend.api.health import router as health_router
from backend.api.matches import create_matches_router
from backend.api.parse_outputs import create_parse_outputs_router
from backend.api.predict import create_predict_router
from backend.api.prediction_runs import create_prediction_runs_router
from backend.api.refresh import create_refresh_router
from backend.api.sync_runs import create_sync_runs_router
from backend.core.config import Settings, get_settings
from backend.database.session import create_session_factory, init_database
from backend.llm.openrouter_prediction import build_default_prediction_provider
from backend.llm.provider import PredictionProvider
from backend.services.prediction_evidence import (
    PredictionEvidenceSynthesizer,
    build_default_prediction_evidence_synthesizer,
)
from backend.services.prediction_guard import InMemoryPredictionGuard, PredictionExecutionGuard
from backend.services.prediction_research import (
    PredictionResearcher,
    build_default_prediction_researcher,
)
from backend.services.refresh import build_default_refresh_pipeline
from backend.services.seed import seed_matches_from_fixture


def create_app(
    settings: Settings | None = None,
    *,
    prediction_provider: PredictionProvider | None = None,
    prediction_researcher: PredictionResearcher | None = None,
    prediction_evidence_synthesizer: PredictionEvidenceSynthesizer | None = None,
    prediction_guard: PredictionExecutionGuard | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    engine, session_factory = create_session_factory(app_settings.database_url)
    refresh_pipeline = build_default_refresh_pipeline(app_settings)
    resolved_prediction_provider = (
        prediction_provider
        if prediction_provider is not None
        else build_default_prediction_provider(app_settings)
    )
    resolved_prediction_researcher = (
        prediction_researcher
        if prediction_researcher is not None
        else build_default_prediction_researcher(app_settings)
    )
    resolved_prediction_evidence_synthesizer = (
        prediction_evidence_synthesizer
        if prediction_evidence_synthesizer is not None
        else build_default_prediction_evidence_synthesizer(app_settings)
    )
    resolved_prediction_guard = (
        prediction_guard if prediction_guard is not None else InMemoryPredictionGuard()
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_database(engine)
        if app_settings.enable_fixture_seed:
            seed_matches_from_fixture(session_factory, app_settings.fixture_seed_path)
        app.state.settings = app_settings
        app.state.session_factory = session_factory
        app.state.refresh_pipeline = refresh_pipeline
        app.state.prediction_provider = resolved_prediction_provider
        app.state.prediction_researcher = resolved_prediction_researcher
        app.state.prediction_evidence_synthesizer = resolved_prediction_evidence_synthesizer
        app.state.prediction_guard = resolved_prediction_guard
        yield
        engine.dispose()

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(create_matches_router(session_factory))
    app.include_router(create_sync_runs_router(session_factory))
    app.include_router(create_parse_outputs_router(session_factory))
    app.include_router(create_prediction_runs_router(session_factory))
    app.include_router(create_evaluations_router(session_factory))
    app.include_router(create_analytics_router(session_factory))
    app.include_router(create_refresh_router(session_factory, app_settings.fixture_seed_path, refresh_pipeline))
    app.include_router(
        create_predict_router(
            session_factory,
            resolved_prediction_provider,
            resolved_prediction_researcher,
            resolved_prediction_evidence_synthesizer,
            resolved_prediction_guard,
        )
    )
    return app


app = create_app()
