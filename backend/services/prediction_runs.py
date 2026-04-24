"""核心功能：编排单次预测执行 run 的创建、状态流转、失败收口与结果关联。"""

import time
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from backend.llm.provider import PredictionProvider
from backend.repositories.prediction_runs import PredictionRunRepository
from backend.services.prediction_decider import decide_prediction
from backend.services.prediction_evidence import (
    PredictionEvidenceSynthesizer,
    synthesize_prediction_evidence,
)
from backend.services.prediction_research import (
    PredictionResearcher,
    run_prediction_research,
)


def run_prediction(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    provider: PredictionProvider | None = None,
    research_executor: PredictionResearcher | None = None,
    evidence_synthesizer: PredictionEvidenceSynthesizer | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    stage_trace: dict[str, dict[str, Any]] = {}
    current_stage: str | None = None

    with session_factory() as session:
        prediction_run = PredictionRunRepository(session).create_running(match_id)

    try:
        with session_factory() as session:
            PredictionRunRepository(session).mark_status(prediction_run.id, "researching")

        current_stage = "research"
        research_started_at = time.perf_counter()
        research = run_prediction_research(
            session_factory,
            match_id,
            researcher=research_executor,
        )
        stage_trace["research"] = _build_research_stage_trace(
            research,
            elapsed_ms=_elapsed_ms(research_started_at),
        )

        with session_factory() as session:
            PredictionRunRepository(session).save_research(
                prediction_run.id,
                planner_model=research.planner_model,
                search_plan_json=research.search_plan,
                search_trace_json=research.search_trace,
                search_documents_json=research.search_documents,
                used_fallback_sources=research.used_fallback_sources,
                stage_trace_json=stage_trace,
                is_full_live_chain=_is_full_live_chain(stage_trace),
                has_any_fallback=_has_any_fallback(stage_trace),
            )

        with session_factory() as session:
            PredictionRunRepository(session).mark_status(prediction_run.id, "synthesizing")

        current_stage = "evidence"
        evidence_started_at = time.perf_counter()
        evidence = synthesize_prediction_evidence(
            session_factory,
            match_id,
            research,
            synthesizer=evidence_synthesizer,
        )
        stage_trace["evidence"] = _build_evidence_stage_trace(
            evidence,
            elapsed_ms=_elapsed_ms(evidence_started_at),
        )

        with session_factory() as session:
            PredictionRunRepository(session).save_evidence(
                prediction_run.id,
                synthesizer_model=evidence.synthesizer_model,
                evidence_bundle_json=evidence.evidence_bundle,
                stage_trace_json=stage_trace,
                is_full_live_chain=_is_full_live_chain(stage_trace),
                has_any_fallback=_has_any_fallback(stage_trace),
            )

        with session_factory() as session:
            PredictionRunRepository(session).mark_status(prediction_run.id, "deciding")

        current_stage = "decider"
        decider_started_at = time.perf_counter()
        created_prediction = decide_prediction(
            session_factory,
            match_id,
            evidence_bundle=evidence.evidence_bundle,
            provider=provider,
        )
        stage_trace["decider"] = {
            "mode": "live",
            "model_name": created_prediction.prediction["model_meta"]["model_name"],
            "elapsed_ms": _elapsed_ms(decider_started_at),
            "error_message": None,
        }
    except Exception as error:
        failed_stage = current_stage or "decider"
        if failed_stage not in stage_trace:
            stage_trace[failed_stage] = {
                "mode": "failed",
                "model_name": None,
                "elapsed_ms": 0,
                "error_message": str(error),
            }
        else:
            stage_trace[failed_stage]["mode"] = "failed"
            stage_trace[failed_stage]["error_message"] = str(error)
        with session_factory() as session:
            PredictionRunRepository(session).mark_failed(
                prediction_run.id,
                error_message=str(error),
                elapsed_ms=_elapsed_ms(started_at),
                stage_trace_json=stage_trace,
                is_full_live_chain=_is_full_live_chain(stage_trace),
                has_any_fallback=_has_any_fallback(stage_trace),
            )
        raise

    with session_factory() as session:
        PredictionRunRepository(session).mark_succeeded(
            prediction_run.id,
            prediction_version_id=created_prediction.prediction_version_id,
            decider_model=created_prediction.prediction["model_meta"]["model_name"],
            elapsed_ms=_elapsed_ms(started_at),
            stage_trace_json=stage_trace,
            is_full_live_chain=_is_full_live_chain(stage_trace),
            has_any_fallback=_has_any_fallback(stage_trace),
        )

    return created_prediction.prediction


def _elapsed_ms(started_at: float) -> int:
    return int(round((time.perf_counter() - started_at) * 1000))


def _build_research_stage_trace(
    research: dict[str, Any] | Any,
    *,
    elapsed_ms: int,
) -> dict[str, Any]:
    planner_model = getattr(research, "planner_model", None)
    search_trace = getattr(research, "search_trace", None)
    fallback_reason = None
    if isinstance(search_trace, dict):
        fallback_reason = str(search_trace.get("fallback_reason") or "").strip() or None

    is_fallback = bool(
        fallback_reason
        or _is_generated_from_local_match_facts(search_trace)
        or _matches_stage_prefix(planner_model, "fake-", "fallback-")
    )
    error_message = fallback_reason
    if error_message is None and _matches_stage_prefix(planner_model, "fake-"):
        error_message = "Live research stage is not configured."

    return {
        "mode": "fallback" if is_fallback else "live",
        "model_name": planner_model,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message,
    }


def _build_evidence_stage_trace(
    evidence: dict[str, Any] | Any,
    *,
    elapsed_ms: int,
) -> dict[str, Any]:
    synthesizer_model = getattr(evidence, "synthesizer_model", None)
    evidence_bundle = getattr(evidence, "evidence_bundle", None)
    fallback_reason = _extract_evidence_fallback_reason(evidence_bundle)
    is_fallback = bool(
        fallback_reason or _matches_stage_prefix(synthesizer_model, "fake-", "fallback-")
    )
    error_message = fallback_reason
    if error_message is None and _matches_stage_prefix(synthesizer_model, "fake-"):
        error_message = "Live evidence stage is not configured."

    return {
        "mode": "fallback" if is_fallback else "live",
        "model_name": synthesizer_model,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message,
    }


def _extract_evidence_fallback_reason(evidence_bundle: Any) -> str | None:
    if not isinstance(evidence_bundle, dict):
        return None

    conflicts = evidence_bundle.get("conflicts")
    if not isinstance(conflicts, list):
        return None

    prefix = "Evidence fallback activated because upstream evidence stage failed: "
    for item in conflicts:
        normalized = str(item).strip()
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip() or None
    return None


def _is_generated_from_local_match_facts(search_trace: Any) -> bool:
    return isinstance(search_trace, dict) and bool(search_trace.get("generated_from_match_facts"))


def _matches_stage_prefix(value: Any, *prefixes: str) -> bool:
    normalized = str(value or "").strip()
    return any(normalized.startswith(prefix) for prefix in prefixes)


def _has_any_fallback(stage_trace: dict[str, dict[str, Any]]) -> bool:
    return any(
        stage_payload.get("mode") == "fallback"
        for stage_name, stage_payload in stage_trace.items()
        if stage_name in {"research", "evidence"}
    )


def _is_full_live_chain(stage_trace: dict[str, dict[str, Any]]) -> bool:
    required_stages = ("research", "evidence", "decider")
    return all(
        isinstance(stage_trace.get(stage_name), dict)
        and stage_trace[stage_name].get("mode") == "live"
        for stage_name in required_stages
    )
