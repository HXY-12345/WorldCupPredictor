"""核心功能：验证 run-based 预测编排会记录 prediction_runs 生命周期并关联最终版本。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.core.config import Settings
from backend.llm.provider import PredictionProviderResponseError
from backend.main import create_app
from backend.models.prediction_run import PredictionRun
from backend.models.prediction_version import PredictionVersion
from backend.services.prediction_evidence import PredictionEvidenceArtifacts
from backend.services.prediction_research import PredictionResearchArtifacts
from backend.services.prediction_runs import run_prediction


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_fixture(path: Path, *, status: str = "not_started") -> None:
    path.write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "id": "fwc2026-m001",
                        "official_match_number": 1,
                        "kickoff_label": "M001",
                        "sort_order": 1,
                        "date": "2026-06-11",
                        "time": "18:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {
                            "name": "Mexico",
                            "flag": "MX",
                            "fifa_rank": 12,
                            "form": ["W", "D", "W"],
                        },
                        "away_team": {
                            "name": "South Africa",
                            "flag": "ZA",
                            "fifa_rank": 47,
                            "form": ["D", "L", "W"],
                        },
                        "status": status,
                        "score": None,
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-03-31T00:00:00Z",
                "total": 1,
            }
        ),
        encoding="utf-8",
    )


class StaticPredictionProvider:
    def predict(self, request):
        match_facts = request.metadata["match_facts"]
        return {
            "predicted_score": {"home": 2, "away": 1},
            "outcome_pick": "home_win",
            "home_goals_pick": 2,
            "away_goals_pick": 1,
            "total_goals_pick": 3,
            "confidence": 76,
            "reasoning_summary": f"Static provider prediction for {match_facts['match_id']}.",
            "evidence_items": [
                {
                    "claim": "Mexico has stronger recent form.",
                    "source_name": "form",
                    "source_url": "https://example.com/form",
                    "source_level": 2,
                },
                {
                    "claim": "Mexico City venue favors the home side.",
                    "source_name": "venue",
                    "source_url": "https://example.com/venue",
                    "source_level": 3,
                },
                {
                    "claim": "South Africa defensive record is mixed.",
                    "source_name": "defense",
                    "source_url": "https://example.com/defense",
                    "source_level": 2,
                },
            ],
            "uncertainties": ["Lineup is not fully confirmed."],
            "model_meta": {
                "provider": "static-test",
                "model_name": "static-test-model",
                "predicted_at": "2026-04-19T12:00:00Z",
            },
            "input_snapshot": match_facts,
        }


class ExplodingPredictionProvider:
    def predict(self, request):
        raise PredictionProviderResponseError("Upstream prediction provider failed.")


class StaticResearchExecutor:
    def run(self, session_factory, match_id):
        return PredictionResearchArtifacts(
            planner_model="openrouter/research-test",
            search_plan={"match_id": match_id, "queries": [{"topic": "preview", "query": "test query"}]},
            search_trace={
                "completed": True,
                "executed_queries": [{"topic": "preview", "query": "test query"}],
                "opened_urls": ["https://example.com/research"],
                "round_count": 1,
            },
            search_documents=[
                {
                    "query": "test query",
                    "title": "Research article",
                    "url": "https://example.com/research",
                    "domain": "example.com",
                    "source_tier": "controlled",
                    "published_at": "2026-04-21T08:00:00Z",
                    "fetched_at": "2026-04-22T01:00:00Z",
                    "content_text": "Research content.",
                    "content_hash": "hash-research",
                }
            ],
            used_fallback_sources=True,
        )


class ExplodingResearchExecutor:
    def run(self, session_factory, match_id):
        raise PredictionProviderResponseError("Research stage failed upstream.")


class StaticEvidenceSynthesizer:
    def synthesize(self, session_factory, match_id, research):
        return PredictionEvidenceArtifacts(
            synthesizer_model="openrouter/evidence-test",
            evidence_bundle={
                "match_id": match_id,
                "home_support": ["主队状态更稳定。"],
                "away_support": ["客队仍有速度优势。"],
                "neutral_factors": ["比赛为揭幕战。"],
                "market_view": ["市场轻微倾向主队。"],
                "conflicts": ["阵容信息存在分歧。"],
                "high_confidence_summary": ["主队略占优。"],
                "document_titles": [document["title"] for document in research.search_documents],
            },
        )


class ExplodingEvidenceSynthesizer:
    def synthesize(self, session_factory, match_id, research):
        raise PredictionProviderResponseError("Evidence synthesis failed upstream.")


def test_run_prediction_creates_succeeded_run_and_links_prediction_version():
    runtime_dir = _runtime_dir("prediction_run_success")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_run_success.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        prediction = run_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            provider=StaticPredictionProvider(),
        )

    assert prediction["confidence"] == 76

    with app.state.session_factory() as session:
        prediction_runs = session.scalars(select(PredictionRun)).all()
        prediction_versions = session.scalars(select(PredictionVersion)).all()

    assert len(prediction_runs) == 1
    assert len(prediction_versions) == 1
    assert prediction_runs[0].match_id == "fwc2026-m001"
    assert prediction_runs[0].status == "succeeded"
    assert prediction_runs[0].prediction_version_id == prediction_versions[0].id
    assert prediction_runs[0].triggered_at is not None
    assert prediction_runs[0].finished_at is not None
    assert prediction_runs[0].elapsed_ms is not None
    assert prediction_runs[0].planner_model == "fake-research-v1"
    assert prediction_runs[0].synthesizer_model == "fake-evidence-v1"
    assert prediction_runs[0].stage_trace_json == {
        "research": {
            "mode": "fallback",
            "model_name": "fake-research-v1",
            "elapsed_ms": prediction_runs[0].stage_trace_json["research"]["elapsed_ms"],
            "error_message": "Live research stage is not configured.",
        },
        "evidence": {
            "mode": "fallback",
            "model_name": "fake-evidence-v1",
            "elapsed_ms": prediction_runs[0].stage_trace_json["evidence"]["elapsed_ms"],
            "error_message": "Live evidence stage is not configured.",
        },
        "decider": {
            "mode": "live",
            "model_name": "static-test-model",
            "elapsed_ms": prediction_runs[0].stage_trace_json["decider"]["elapsed_ms"],
            "error_message": None,
        },
    }
    assert prediction_runs[0].is_full_live_chain is False
    assert prediction_runs[0].has_any_fallback is True
    assert prediction_runs[0].document_count >= 4
    assert prediction_runs[0].used_fallback_sources is False
    assert prediction_runs[0].search_plan_json is not None
    assert prediction_runs[0].search_trace_json is not None
    assert prediction_runs[0].search_documents_json is not None
    assert prediction_runs[0].evidence_bundle_json is not None
    assert len(prediction_runs[0].search_documents_json) >= 4
    assert prediction_runs[0].search_trace_json["generated_from_match_facts"] is True
    assert prediction_runs[0].stage_trace_json["research"]["elapsed_ms"] >= 0
    assert prediction_runs[0].stage_trace_json["evidence"]["elapsed_ms"] >= 0
    assert prediction_runs[0].stage_trace_json["decider"]["elapsed_ms"] >= 0


def test_run_prediction_marks_failed_run_without_persisting_prediction_version():
    runtime_dir = _runtime_dir("prediction_run_failure")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_run_failure.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        try:
            run_prediction(
                app.state.session_factory,
                "fwc2026-m001",
                provider=ExplodingPredictionProvider(),
            )
        except PredictionProviderResponseError:
            pass
        else:
            raise AssertionError("Expected provider failure to bubble up from run_prediction.")

    with app.state.session_factory() as session:
        prediction_runs = session.scalars(select(PredictionRun)).all()
        prediction_version_count = session.scalar(select(func.count()).select_from(PredictionVersion))

    assert len(prediction_runs) == 1
    assert prediction_runs[0].status == "failed"
    assert prediction_runs[0].prediction_version_id is None
    assert "Upstream prediction provider failed." in (prediction_runs[0].error_message or "")
    assert prediction_runs[0].finished_at is not None
    assert prediction_runs[0].stage_trace_json["research"]["mode"] == "fallback"
    assert prediction_runs[0].stage_trace_json["evidence"]["mode"] == "fallback"
    assert prediction_runs[0].stage_trace_json["decider"]["mode"] == "failed"
    assert prediction_runs[0].stage_trace_json["decider"]["model_name"] is None
    assert "Upstream prediction provider failed." in prediction_runs[0].stage_trace_json["decider"]["error_message"]
    assert prediction_runs[0].is_full_live_chain is False
    assert prediction_runs[0].has_any_fallback is True
    assert prediction_version_count == 0


def test_run_prediction_records_injected_research_and_evidence_stage_models():
    runtime_dir = _runtime_dir("prediction_run_real_stages")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_run_real_stages.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        run_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            provider=StaticPredictionProvider(),
            research_executor=StaticResearchExecutor(),
            evidence_synthesizer=StaticEvidenceSynthesizer(),
        )

    with app.state.session_factory() as session:
        prediction_run = session.scalars(select(PredictionRun)).one()

    assert prediction_run.status == "succeeded"
    assert prediction_run.planner_model == "openrouter/research-test"
    assert prediction_run.synthesizer_model == "openrouter/evidence-test"
    assert prediction_run.document_count == 1
    assert prediction_run.used_fallback_sources is True
    assert prediction_run.stage_trace_json == {
        "research": {
            "mode": "live",
            "model_name": "openrouter/research-test",
            "elapsed_ms": prediction_run.stage_trace_json["research"]["elapsed_ms"],
            "error_message": None,
        },
        "evidence": {
            "mode": "live",
            "model_name": "openrouter/evidence-test",
            "elapsed_ms": prediction_run.stage_trace_json["evidence"]["elapsed_ms"],
            "error_message": None,
        },
        "decider": {
            "mode": "live",
            "model_name": "static-test-model",
            "elapsed_ms": prediction_run.stage_trace_json["decider"]["elapsed_ms"],
            "error_message": None,
        },
    }
    assert prediction_run.is_full_live_chain is True
    assert prediction_run.has_any_fallback is False


def test_run_prediction_falls_back_to_local_evidence_when_real_synthesizer_fails():
    runtime_dir = _runtime_dir("prediction_run_evidence_fallback")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_run_evidence_fallback.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        prediction = run_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            provider=StaticPredictionProvider(),
            research_executor=StaticResearchExecutor(),
            evidence_synthesizer=ExplodingEvidenceSynthesizer(),
        )

    assert prediction["confidence"] == 76

    with app.state.session_factory() as session:
        prediction_run = session.scalars(select(PredictionRun)).one()

    assert prediction_run.status == "succeeded"
    assert prediction_run.synthesizer_model == "fallback-evidence-v1"
    assert "Evidence fallback activated" in " ".join(prediction_run.evidence_bundle_json["conflicts"])
    assert prediction_run.stage_trace_json["research"]["mode"] == "live"
    assert prediction_run.stage_trace_json["evidence"]["mode"] == "fallback"
    assert prediction_run.stage_trace_json["decider"]["mode"] == "live"
    assert prediction_run.stage_trace_json["evidence"]["model_name"] == "fallback-evidence-v1"
    assert "Evidence synthesis failed upstream." in prediction_run.stage_trace_json["evidence"]["error_message"]
    assert prediction_run.is_full_live_chain is False
    assert prediction_run.has_any_fallback is True


def test_run_prediction_falls_back_to_local_research_when_real_research_fails():
    runtime_dir = _runtime_dir("prediction_run_research_fallback")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_run_research_fallback.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
        openrouter_model_config_path=None,
        openrouter_key_path=None,
        prediction_openrouter_model_config_path=None,
        prediction_openrouter_key_path=None,
        prediction_research_openrouter_model_config_path=None,
        prediction_research_openrouter_key_path=None,
        prediction_evidence_openrouter_model_config_path=None,
        prediction_evidence_openrouter_key_path=None,
    )
    app = create_app(settings)

    with TestClient(app):
        prediction = run_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            provider=StaticPredictionProvider(),
            research_executor=ExplodingResearchExecutor(),
            evidence_synthesizer=StaticEvidenceSynthesizer(),
        )

    assert prediction["confidence"] == 76

    with app.state.session_factory() as session:
        prediction_run = session.scalars(select(PredictionRun)).one()

    assert prediction_run.status == "succeeded"
    assert prediction_run.planner_model == "fallback-research-v1"
    assert prediction_run.used_fallback_sources is True
    assert prediction_run.document_count >= 4
    assert prediction_run.search_trace_json["generated_from_match_facts"] is True
    assert prediction_run.search_trace_json["fallback_mode"] == "local_match_fact_synthesis"
    assert prediction_run.stage_trace_json["research"]["mode"] == "fallback"
    assert prediction_run.stage_trace_json["research"]["model_name"] == "fallback-research-v1"
    assert "Research stage failed upstream." in prediction_run.stage_trace_json["research"]["error_message"]
    assert prediction_run.stage_trace_json["evidence"]["mode"] == "live"
    assert prediction_run.stage_trace_json["decider"]["mode"] == "live"
    assert prediction_run.is_full_live_chain is False
    assert prediction_run.has_any_fallback is True
