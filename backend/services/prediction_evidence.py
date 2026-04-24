"""核心功能：定义预测前 evidence 阶段的统一合同，支持 fake 与 OpenRouter 两种实现。"""

from dataclasses import dataclass
import json
from pathlib import Path
from threading import Thread
from typing import Any, Protocol

import httpx
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterClient, OpenRouterSettings, load_openrouter_settings
from backend.llm.provider import (
    PredictionProviderError,
    PredictionProviderConfigError,
    PredictionProviderResponseError,
    PredictionProviderTimeoutError,
)
from backend.services.prediction_context import build_prediction_context
from backend.services.prediction_research import PredictionResearchArtifacts
from backend.services.structured_output import extract_json_object_text


@dataclass(frozen=True)
class PredictionEvidenceArtifacts:
    synthesizer_model: str | None
    evidence_bundle: dict[str, Any]


class PredictionEvidenceSynthesizer(Protocol):
    def synthesize(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
        research: PredictionResearchArtifacts,
    ) -> PredictionEvidenceArtifacts:
        ...


class FakePredictionEvidenceSynthesizer:
    def synthesize(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
        research: PredictionResearchArtifacts,
    ) -> PredictionEvidenceArtifacts:
        prediction_context = build_prediction_context(session_factory, match_id)
        match_facts = prediction_context.match_facts
        home_team = (match_facts.get("home_team") or {}).get("name") or "Home Team"
        away_team = (match_facts.get("away_team") or {}).get("name") or "Away Team"
        venue = match_facts.get("venue") or "Unknown Venue"

        evidence_bundle = {
            "match_id": match_id,
            "home_support": [
                f"{home_team} recent form is available in the research bundle and looks steadier.",
                f"{home_team} benefits from the venue context at {venue}.",
            ],
            "away_support": [
                f"{away_team} still carries attacking threat in the preview material.",
            ],
            "neutral_factors": [
                f"The match remains in pre-kickoff status and belongs to {match_facts.get('stage') or 'Unknown Stage'}.",
            ],
            "market_view": [
                f"Current fake research does not activate fallback sources for {home_team} vs {away_team}.",
            ],
            "conflicts": [],
            "high_confidence_summary": [
                f"{home_team} carries the stronger pre-match profile in the current evidence bundle.",
            ],
            "document_titles": [document["title"] for document in research.search_documents],
        }

        return PredictionEvidenceArtifacts(
            synthesizer_model="fake-evidence-v1",
            evidence_bundle=evidence_bundle,
        )


class OpenRouterPredictionEvidenceSynthesizer:
    """使用 OpenRouter 将 research 全文压缩为结构化证据包。"""

    def __init__(
        self,
        settings: OpenRouterSettings,
        *,
        client: OpenRouterClient | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds
        self.client = client or OpenRouterClient(settings, timeout_seconds=timeout_seconds)

    @classmethod
    def from_config(
        cls,
        model_config_path: str,
        key_path: str,
        *,
        timeout_seconds: float = 90.0,
    ) -> "OpenRouterPredictionEvidenceSynthesizer":
        try:
            settings = load_openrouter_settings(model_config_path, key_path)
        except ValueError as error:
            raise PredictionProviderConfigError(str(error)) from error
        return cls(settings, timeout_seconds=timeout_seconds)

    def synthesize(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
        research: PredictionResearchArtifacts,
    ) -> PredictionEvidenceArtifacts:
        prediction_context = build_prediction_context(session_factory, match_id)

        try:
            payload = _run_completion_with_timeout(
                self.client,
                timeout_seconds=self.timeout_seconds,
                messages=_build_evidence_messages(prediction_context.match_facts, research),
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "prediction_evidence_bundle",
                        "strict": True,
                        "schema": _evidence_response_schema(),
                    },
                },
                plugins=_openrouter_plugins(
                    enable_web_plugin=self.settings.enable_web_plugin,
                    enable_response_healing=self.settings.enable_response_healing,
                ),
                provider={"require_parameters": self.settings.require_parameters},
            )
        except httpx.TimeoutException as error:
            raise PredictionProviderTimeoutError(f"OpenRouter evidence request timed out: {error}") from error
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else "unknown"
            response_text = error.response.text if error.response is not None else str(error)
            raise PredictionProviderResponseError(
                f"OpenRouter evidence request failed with status {status_code}: {response_text}"
            ) from error
        except httpx.HTTPError as error:
            raise PredictionProviderResponseError(f"OpenRouter evidence request failed: {error}") from error
        except json.JSONDecodeError as error:
            raise PredictionProviderResponseError("OpenRouter evidence response was not valid JSON.") from error

        completion_text = _extract_completion_text(payload)
        try:
            raw_evidence = json.loads(extract_json_object_text(completion_text))
        except json.JSONDecodeError as error:
            raise PredictionProviderResponseError("OpenRouter evidence response was not valid JSON.") from error

        evidence_bundle = _normalize_evidence_payload(
            match_id,
            raw_evidence,
            research=research,
        )
        return PredictionEvidenceArtifacts(
            synthesizer_model=payload.get("model") or self.settings.model,
            evidence_bundle=evidence_bundle,
        )


def build_default_prediction_evidence_synthesizer(settings: Settings) -> PredictionEvidenceSynthesizer:
    model_config_path = settings.prediction_evidence_openrouter_model_config_path
    key_path = settings.prediction_evidence_openrouter_key_path

    if not model_config_path or not key_path:
        return FakePredictionEvidenceSynthesizer()
    if not Path(model_config_path).exists() or not Path(key_path).exists():
        return FakePredictionEvidenceSynthesizer()

    try:
        return OpenRouterPredictionEvidenceSynthesizer.from_config(
            model_config_path,
            key_path,
            timeout_seconds=settings.prediction_evidence_request_timeout_seconds,
        )
    except PredictionProviderConfigError:
        return FakePredictionEvidenceSynthesizer()


def synthesize_prediction_evidence(
    session_factory: sessionmaker[Session],
    match_id: str,
    research: PredictionResearchArtifacts,
    *,
    synthesizer: PredictionEvidenceSynthesizer | None = None,
) -> PredictionEvidenceArtifacts:
    active_synthesizer = synthesizer or FakePredictionEvidenceSynthesizer()
    try:
        return active_synthesizer.synthesize(session_factory, match_id, research)
    except PredictionProviderError as error:
        if isinstance(active_synthesizer, FakePredictionEvidenceSynthesizer):
            raise
        return _build_fallback_prediction_evidence(session_factory, match_id, research, str(error))


def synthesize_fake_prediction_evidence(
    session_factory: sessionmaker[Session],
    match_id: str,
    research: PredictionResearchArtifacts,
) -> PredictionEvidenceArtifacts:
    return FakePredictionEvidenceSynthesizer().synthesize(session_factory, match_id, research)


def _build_fallback_prediction_evidence(
    session_factory: sessionmaker[Session],
    match_id: str,
    research: PredictionResearchArtifacts,
    error_message: str,
) -> PredictionEvidenceArtifacts:
    fallback = FakePredictionEvidenceSynthesizer().synthesize(session_factory, match_id, research)
    evidence_bundle = dict(fallback.evidence_bundle)
    evidence_bundle["conflicts"] = _merge_string_lists(
        _normalize_string_list(evidence_bundle.get("conflicts")),
        [f"Evidence fallback activated because upstream evidence stage failed: {error_message}"],
    )
    evidence_bundle["document_titles"] = _merge_string_lists(
        _normalize_string_list(evidence_bundle.get("document_titles")),
        _research_document_titles(research),
    )
    return PredictionEvidenceArtifacts(
        synthesizer_model="fallback-evidence-v1",
        evidence_bundle=evidence_bundle,
    )


def _build_evidence_messages(
    match_facts: dict[str, Any],
    research: PredictionResearchArtifacts,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You synthesize football pre-match research into a compact evidence bundle.\n"
                "Do not browse additional sources.\n"
                "Do not reference or use any historical prediction versions.\n"
                "Write all natural-language output in Simplified Chinese.\n"
                "Return only valid JSON matching the provided schema."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": "synthesize_evidence",
                    "match_facts": match_facts,
                    "search_plan": research.search_plan,
                    "search_trace": research.search_trace,
                    "search_documents": research.search_documents,
                    "requirements": [
                        "Balance evidence that supports home, away, and neutral interpretations.",
                        "Include market_view only as a secondary signal, not as a decisive factor.",
                        "Surface conflicts and uncertainty explicitly.",
                        "high_confidence_summary should contain concise Chinese sentences that the final decider can reuse.",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
        },
    ]


def _evidence_response_schema() -> dict[str, Any]:
    string_list = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "match_id": {"type": "string"},
            "home_support": string_list,
            "away_support": string_list,
            "neutral_factors": string_list,
            "market_view": string_list,
            "conflicts": string_list,
            "high_confidence_summary": string_list,
            "document_titles": string_list,
        },
        "required": [
            "match_id",
            "home_support",
            "away_support",
            "neutral_factors",
            "market_view",
            "conflicts",
            "high_confidence_summary",
            "document_titles",
        ],
        "additionalProperties": False,
    }


def _openrouter_plugins(enable_web_plugin: bool, enable_response_healing: bool) -> list[dict[str, Any]]:
    plugins: list[dict[str, Any]] = []
    if enable_web_plugin:
        plugins.append({"id": "web"})
    if enable_response_healing:
        plugins.append({"id": "response-healing"})
    return plugins


def _extract_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise PredictionProviderResponseError("OpenRouter evidence response did not include any choices.")

    message = choices[0].get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        if text_parts:
            return "".join(text_parts)

    raise PredictionProviderResponseError("OpenRouter evidence response content was not parseable text.")


def _normalize_evidence_payload(
    match_id: str,
    raw_evidence: dict[str, Any],
    *,
    research: PredictionResearchArtifacts | None = None,
) -> dict[str, Any]:
    if not isinstance(raw_evidence, dict):
        raise PredictionProviderResponseError("OpenRouter evidence response must be a JSON object.")

    normalized = {
        "match_id": _normalize_match_id(raw_evidence.get("match_id"), match_id),
        "home_support": _normalize_string_list(raw_evidence.get("home_support")),
        "away_support": _normalize_string_list(raw_evidence.get("away_support")),
        "neutral_factors": _normalize_string_list(raw_evidence.get("neutral_factors")),
        "market_view": _normalize_string_list(raw_evidence.get("market_view")),
        "conflicts": _normalize_string_list(raw_evidence.get("conflicts")),
        "high_confidence_summary": _normalize_string_list(raw_evidence.get("high_confidence_summary")),
        "document_titles": _normalize_string_list(raw_evidence.get("document_titles")),
    }

    evidence_analysis = _coerce_dict(raw_evidence.get("evidence_analysis"))
    evidence_summary = _coerce_dict(raw_evidence.get("evidence_summary"))
    nested_bundle = _coerce_dict(raw_evidence.get("evidence_bundle"))
    match_logistics = _coerce_dict(nested_bundle.get("match_logistics"))
    team_profiles = _coerce_dict(nested_bundle.get("team_profiles"))

    normalized["home_support"] = _merge_string_lists(
        normalized["home_support"],
        _normalize_string_list(evidence_analysis.get("home_advantage")),
        _normalize_string_list(evidence_summary.get("home_team_form")),
        _summarize_team_profile(team_profiles.get("mexico"), label="Mexico"),
    )
    normalized["away_support"] = _merge_string_lists(
        normalized["away_support"],
        _normalize_string_list(evidence_analysis.get("away_analysis")),
        _normalize_string_list(evidence_summary.get("away_team_form")),
        _summarize_team_profile(team_profiles.get("south_africa"), label="South Africa"),
    )
    normalized["neutral_factors"] = _merge_string_lists(
        normalized["neutral_factors"],
        _normalize_string_list(evidence_analysis.get("neutral_factors")),
        _normalize_string_list(evidence_analysis.get("neutral_perspective")),
        _normalize_string_list(evidence_summary.get("h2h_history")),
        _normalize_string_list(evidence_summary.get("key_factors")),
        _summarize_match_logistics(match_logistics),
        _summarize_historical_h2h(nested_bundle.get("historical_h2h")),
    )
    normalized["market_view"] = _merge_string_lists(
        normalized["market_view"],
        _normalize_string_list(raw_evidence.get("market_view")),
        _normalize_string_list(raw_evidence.get("search_status")),
    )
    normalized["conflicts"] = _merge_string_lists(
        normalized["conflicts"],
        _normalize_string_list(raw_evidence.get("uncertainties")),
        _normalize_string_list(raw_evidence.get("source_conflicts")),
        _normalize_string_list(raw_evidence.get("uncertainties_and_conflicts")),
        _normalize_string_list(raw_evidence.get("conflicts_and_uncertainty")),
    )
    normalized["high_confidence_summary"] = _merge_string_lists(
        normalized["high_confidence_summary"],
        _normalize_string_list(raw_evidence.get("high_confidence_summary")),
    )
    normalized["document_titles"] = _merge_string_lists(
        normalized["document_titles"],
        _extract_titles_from_sources(raw_evidence.get("sources")),
        _research_document_titles(research),
    )

    return normalized


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if not isinstance(value, list):
        return []

    return [normalized for item in value if (normalized := str(item).strip())]


def _normalize_match_id(value: Any, fallback_match_id: str) -> str:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    return fallback_match_id


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _merge_string_lists(*values: list[str]) -> list[str]:
    merged: list[str] = []
    for value in values:
        for item in value:
            if item and item not in merged:
                merged.append(item)
    return merged


def _summarize_team_profile(value: Any, *, label: str) -> list[str]:
    profile = _coerce_dict(value)
    if not profile:
        return []

    parts: list[str] = []
    coach = str(profile.get("coach") or "").strip()
    recent_form = str(profile.get("recent_form") or "").strip()
    key_player = str(profile.get("key_player") or "").strip()
    squad_composition = str(profile.get("squad_composition") or "").strip()
    wc_history = str(profile.get("wc_history") or "").strip()

    if coach:
        parts.append(f"{label} coach: {coach}.")
    if recent_form:
        parts.append(f"{label} recent form: {recent_form}.")
    if key_player:
        parts.append(f"{label} key player: {key_player}.")
    if squad_composition:
        parts.append(f"{label} squad composition: {squad_composition}.")
    if wc_history:
        parts.append(f"{label} World Cup history: {wc_history}.")
    return parts


def _summarize_match_logistics(value: Any) -> list[str]:
    logistics = _coerce_dict(value)
    if not logistics:
        return []

    parts: list[str] = []
    date = str(logistics.get("date") or "").strip()
    venue = str(logistics.get("venue") or "").strip()
    group = str(logistics.get("group") or "").strip()
    other_groups = _normalize_string_list(logistics.get("other_groups"))

    if date:
        parts.append(f"Match date reference: {date}.")
    if venue:
        parts.append(f"Venue context: {venue}.")
    if group:
        parts.append(f"Competition group: {group}.")
    if other_groups:
        parts.append(f"Related group teams: {', '.join(other_groups)}.")
    return parts


def _summarize_historical_h2h(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    parts: list[str] = []
    for item in value:
        payload = _coerce_dict(item)
        if not payload:
            continue
        year = str(payload.get("year") or "").strip()
        tournament = str(payload.get("tournament") or "").strip()
        result = str(payload.get("result") or "").strip()
        sentence = " ".join(part for part in [year, tournament, result] if part).strip()
        if sentence:
            parts.append(sentence + ".")
    return parts


def _extract_titles_from_sources(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    titles: list[str] = []
    for item in value:
        payload = _coerce_dict(item)
        title = str(payload.get("title") or payload.get("domain") or payload.get("url") or "").strip()
        if title and title not in titles:
            titles.append(title)
    return titles


def _research_document_titles(research: PredictionResearchArtifacts | None) -> list[str]:
    if research is None:
        return []

    titles: list[str] = []
    for item in research.search_documents:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("domain") or item.get("url") or "").strip()
        if title and title not in titles:
            titles.append(title)
    return titles


def _run_completion_with_timeout(
    client: OpenRouterClient | Any,
    *,
    timeout_seconds: float,
    **kwargs: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    captured_error: list[BaseException] = []

    def target() -> None:
        try:
            result["payload"] = client.create_chat_completion(**kwargs)
        except BaseException as error:  # pragma: no cover - propagated after join
            captured_error.append(error)

    thread = Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        raise PredictionProviderTimeoutError("OpenRouter evidence request timed out.")
    if captured_error:
        raise captured_error[0]
    return result["payload"]
