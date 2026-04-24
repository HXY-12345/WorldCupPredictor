"""核心功能：定义预测前 research 阶段的统一合同，支持 fake 与 OpenRouter 两种实现。"""

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from threading import Thread
from typing import Any, Protocol
from urllib.parse import urlparse

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
from backend.services.duckduckgo_search import DuckDuckGoSearchError, DuckDuckGoSearchTool
from backend.services.prediction_context import build_prediction_context
from backend.services.structured_output import extract_json_object_text


@dataclass(frozen=True)
class PredictionResearchArtifacts:
    planner_model: str | None
    search_plan: dict[str, Any]
    search_trace: dict[str, Any]
    search_documents: list[dict[str, Any]]
    used_fallback_sources: bool


class PredictionResearcher(Protocol):
    def run(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
    ) -> PredictionResearchArtifacts:
        ...


class FakePredictionResearcher:
    def run(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
    ) -> PredictionResearchArtifacts:
        prediction_context = build_prediction_context(session_factory, match_id)
        match_facts = prediction_context.match_facts
        queries, documents, search_trace = _build_local_research_bundle(match_id, match_facts)

        return PredictionResearchArtifacts(
            planner_model="fake-research-v1",
            search_plan={
                "match_id": match_id,
                "queries": queries,
                "source_policy": "controlled-local-synthesis",
            },
            search_trace=search_trace,
            search_documents=documents,
            used_fallback_sources=False,
        )


class OpenRouterPredictionResearcher:
    """使用 OpenRouter Web 能力执行单场比赛的赛前 research。"""

    def __init__(
        self,
        settings: OpenRouterSettings,
        *,
        client: OpenRouterClient | None = None,
        timeout_seconds: float = 120.0,
        search_tool: DuckDuckGoSearchTool | Any | None = None,
        max_tool_rounds: int = 4,
    ) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds
        self.client = client or OpenRouterClient(settings, timeout_seconds=timeout_seconds)
        self.search_tool = search_tool or DuckDuckGoSearchTool()
        self.max_tool_rounds = max_tool_rounds

    @classmethod
    def from_config(
        cls,
        model_config_path: str,
        key_path: str,
        *,
        timeout_seconds: float = 120.0,
        search_tool: DuckDuckGoSearchTool | Any | None = None,
        max_tool_rounds: int = 4,
    ) -> "OpenRouterPredictionResearcher":
        try:
            settings = load_openrouter_settings(model_config_path, key_path)
        except ValueError as error:
            raise PredictionProviderConfigError(str(error)) from error
        return cls(
            settings,
            timeout_seconds=timeout_seconds,
            search_tool=search_tool,
            max_tool_rounds=max_tool_rounds,
        )

    def run(
        self,
        session_factory: sessionmaker[Session],
        match_id: str,
    ) -> PredictionResearchArtifacts:
        prediction_context = build_prediction_context(session_factory, match_id)
        match_facts = prediction_context.match_facts

        try:
            payload, tool_trace = _run_research_tool_loop(
                self.client,
                match_facts=match_facts,
                timeout_seconds=self.timeout_seconds,
                plugins=_openrouter_plugins(
                    enable_web_plugin=self.settings.enable_web_plugin,
                    enable_response_healing=self.settings.enable_response_healing,
                ),
                provider={"require_parameters": self.settings.require_parameters},
                search_tool=self.search_tool,
                max_tool_rounds=self.max_tool_rounds,
            )
        except httpx.TimeoutException as error:
            raise PredictionProviderTimeoutError(f"OpenRouter research request timed out: {error}") from error
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else "unknown"
            response_text = error.response.text if error.response is not None else str(error)
            raise PredictionProviderResponseError(
                f"OpenRouter research request failed with status {status_code}: {response_text}"
            ) from error
        except httpx.HTTPError as error:
            raise PredictionProviderResponseError(f"OpenRouter research request failed: {error}") from error
        except DuckDuckGoSearchError as error:
            raise PredictionProviderResponseError(f"DuckDuckGo search failed: {error}") from error
        except json.JSONDecodeError as error:
            raise PredictionProviderResponseError("OpenRouter research response was not valid JSON.") from error

        completion_text = _extract_completion_text(payload)
        try:
            raw_research = json.loads(extract_json_object_text(completion_text))
        except (json.JSONDecodeError, ValueError) as error:
            raise PredictionProviderResponseError("OpenRouter research response was not valid JSON.") from error

        normalized_research = _normalize_research_payload(match_id, raw_research)
        if tool_trace["round_count"] > 0:
            normalized_research["search_trace"] = _merge_tool_search_trace(
                normalized_research["search_trace"],
                tool_trace,
            )
            normalized_research["search_documents"] = list(tool_trace["search_documents"])
        return PredictionResearchArtifacts(
            planner_model=payload.get("model") or self.settings.model,
            search_plan=normalized_research["search_plan"],
            search_trace=normalized_research["search_trace"],
            search_documents=normalized_research["search_documents"],
            used_fallback_sources=normalized_research["used_fallback_sources"],
        )


def build_default_prediction_researcher(settings: Settings) -> PredictionResearcher:
    model_config_path = settings.prediction_research_openrouter_model_config_path
    key_path = settings.prediction_research_openrouter_key_path

    if (
        not settings.prediction_research_duckduckgo_enabled
        or not model_config_path
        or not key_path
    ):
        return FakePredictionResearcher()
    if not Path(model_config_path).exists() or not Path(key_path).exists():
        return FakePredictionResearcher()

    try:
        return OpenRouterPredictionResearcher.from_config(
            model_config_path,
            key_path,
            timeout_seconds=settings.prediction_research_request_timeout_seconds,
            search_tool=DuckDuckGoSearchTool(
                timeout_seconds=settings.prediction_research_duckduckgo_timeout_seconds,
                max_results_limit=settings.prediction_research_duckduckgo_max_results_per_query,
                backend=settings.prediction_research_duckduckgo_backend,
            ),
            max_tool_rounds=settings.prediction_research_duckduckgo_max_rounds,
        )
    except PredictionProviderConfigError:
        return FakePredictionResearcher()


def run_prediction_research(
    session_factory: sessionmaker[Session],
    match_id: str,
    *,
    researcher: PredictionResearcher | None = None,
) -> PredictionResearchArtifacts:
    active_researcher = researcher or FakePredictionResearcher()
    try:
        return active_researcher.run(session_factory, match_id)
    except PredictionProviderError as error:
        if isinstance(active_researcher, FakePredictionResearcher):
            raise
        fallback = FakePredictionResearcher().run(session_factory, match_id)
        return PredictionResearchArtifacts(
            planner_model="fallback-research-v1",
            search_plan=fallback.search_plan,
            search_trace={
                **fallback.search_trace,
                "fallback_reason": str(error),
            },
            search_documents=fallback.search_documents,
            used_fallback_sources=True,
        )


def run_fake_prediction_research(
    session_factory: sessionmaker[Session],
    match_id: str,
) -> PredictionResearchArtifacts:
    return FakePredictionResearcher().run(session_factory, match_id)


def _build_document(
    *,
    query: str,
    title: str,
    url: str,
    domain: str,
    source_tier: str,
    fetched_at: str,
    content_text: str,
) -> dict[str, Any]:
    return {
        "query": query,
        "title": title,
        "url": url,
        "domain": domain,
        "source_tier": source_tier,
        "published_at": None,
        "fetched_at": fetched_at,
        "content_text": content_text,
        "content_hash": hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
    }


def _build_local_research_bundle(
    match_id: str,
    match_facts: dict[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, Any]], dict[str, Any]]:
    home_team_payload = match_facts.get("home_team") or {}
    away_team_payload = match_facts.get("away_team") or {}
    home_team = home_team_payload.get("name") or "Home Team"
    away_team = away_team_payload.get("name") or "Away Team"
    venue = str(match_facts.get("venue") or "Unknown Venue")
    stage = str(match_facts.get("stage") or "Unknown Stage")
    group_name = str(match_facts.get("group_name") or "").strip()
    kickoff_reference = _build_kickoff_reference(match_facts)
    fetched_at = datetime.now(UTC).isoformat()

    queries = [
        {
            "topic": "match_preview",
            "query": f"{home_team} vs {away_team} {stage} preview {venue}",
        },
        {
            "topic": "home_team_form",
            "query": f"{home_team} recent form FIFA ranking squad news",
        },
        {
            "topic": "away_team_form",
            "query": f"{away_team} recent form FIFA ranking squad news",
        },
        {
            "topic": "venue_context",
            "query": f"{venue} stadium context travel conditions {home_team} {away_team}",
        },
        {
            "topic": "availability_watch",
            "query": f"{home_team} {away_team} predicted lineups injuries availability",
        },
    ]

    preview_summary = (
        f"{home_team} will face {away_team} in {stage}{_group_suffix(group_name)} at {venue}. "
        f"Kickoff reference: {kickoff_reference}. Match label: {match_facts.get('kickoff_label') or 'TBD'}. "
        f"Current status: {match_facts.get('status') or 'unknown'}. {_build_rank_comparison(home_team_payload, away_team_payload)}"
    ).strip()
    documents = [
        _build_document(
            query=queries[0]["query"],
            title=f"{home_team} vs {away_team} local preview digest",
            url=f"https://research.worldcup.invalid/{match_id}/preview",
            domain="research.worldcup.invalid",
            source_tier="controlled",
            fetched_at=fetched_at,
            content_text=preview_summary,
        ),
        _build_document(
            query=queries[1]["query"],
            title=f"{home_team} local team profile",
            url=f"https://research.worldcup.invalid/{match_id}/home-team-form",
            domain="research.worldcup.invalid",
            source_tier="controlled",
            fetched_at=fetched_at,
            content_text=(
                f"{home_team} profile from local match facts. {_build_team_rank_sentence(home_team, home_team_payload)} "
                f"{_build_team_form_sentence(home_team, home_team_payload)}"
            ).strip(),
        ),
        _build_document(
            query=queries[2]["query"],
            title=f"{away_team} local team profile",
            url=f"https://research.worldcup.invalid/{match_id}/away-team-form",
            domain="research.worldcup.invalid",
            source_tier="controlled",
            fetched_at=fetched_at,
            content_text=(
                f"{away_team} profile from local match facts. {_build_team_rank_sentence(away_team, away_team_payload)} "
                f"{_build_team_form_sentence(away_team, away_team_payload)}"
            ).strip(),
        ),
        _build_document(
            query=queries[3]["query"],
            title=f"{venue} venue and stage context",
            url=f"https://research.worldcup.invalid/{match_id}/venue-context",
            domain="research.worldcup.invalid",
            source_tier="controlled",
            fetched_at=fetched_at,
            content_text=(
                f"Venue context digest for {home_team} vs {away_team}. "
                f"The match belongs to {stage}{_group_suffix(group_name)} and is scheduled for {kickoff_reference}. "
                f"Official match number: {match_facts.get('official_match_number') or 'unknown'}."
            ).strip(),
        ),
        _build_document(
            query=queries[4]["query"],
            title=f"{home_team} vs {away_team} availability watch",
            url=f"https://research.worldcup.invalid/{match_id}/availability-watch",
            domain="research.worldcup.invalid",
            source_tier="controlled",
            fetched_at=fetched_at,
            content_text=(
                f"Availability watch generated from local match facts only. "
                f"No confirmed lineups, injuries, or suspensions are stored in the local dataset for {home_team} vs {away_team}. "
                f"This item should trigger live verification before kickoff at {kickoff_reference}."
            ).strip(),
        ),
    ]
    search_trace = {
        "completed": True,
        "executed_queries": queries,
        "opened_urls": [document["url"] for document in documents],
        "round_count": 1,
        "generated_from_match_facts": True,
        "fallback_mode": "local_match_fact_synthesis",
    }
    return queries, documents, search_trace


def _group_suffix(group_name: str) -> str:
    normalized = group_name.strip()
    if not normalized:
        return ""
    return f", Group {normalized}"


def _build_kickoff_reference(match_facts: dict[str, Any]) -> str:
    date = str(match_facts.get("date") or "").strip()
    time_label = str(match_facts.get("time") or "").strip()
    if date and time_label:
        return f"{date} {time_label}"
    if date:
        return date
    if time_label:
        return time_label
    return "TBD"


def _build_team_rank_sentence(team_name: str, team_payload: dict[str, Any]) -> str:
    fifa_rank = team_payload.get("fifa_rank")
    if fifa_rank in (None, ""):
        return f"{team_name} FIFA rank is unavailable."
    return f"{team_name} FIFA rank: {fifa_rank}."


def _build_team_form_sentence(team_name: str, team_payload: dict[str, Any]) -> str:
    form = _normalize_form_list(team_payload.get("form"))
    if not form:
        return f"{team_name} recent form is unavailable."

    wins = sum(1 for item in form if item == "W")
    draws = sum(1 for item in form if item == "D")
    losses = sum(1 for item in form if item == "L")
    return (
        f"{team_name} recent form sequence: {'-'.join(form)}. "
        f"Record in stored sample: {wins} wins, {draws} draws, {losses} losses."
    )


def _build_rank_comparison(home_team_payload: dict[str, Any], away_team_payload: dict[str, Any]) -> str:
    home_name = str(home_team_payload.get("name") or "Home Team")
    away_name = str(away_team_payload.get("name") or "Away Team")
    home_rank = home_team_payload.get("fifa_rank")
    away_rank = away_team_payload.get("fifa_rank")
    if home_rank in (None, "") or away_rank in (None, ""):
        return "FIFA rank comparison is incomplete in the local dataset."

    try:
        home_rank_value = int(home_rank)
        away_rank_value = int(away_rank)
    except (TypeError, ValueError):
        return "FIFA rank comparison is incomplete in the local dataset."

    if home_rank_value == away_rank_value:
        return f"FIFA rank comparison is level at {home_rank_value} for both teams."

    favored_team = home_name if home_rank_value < away_rank_value else away_name
    rank_gap = abs(home_rank_value - away_rank_value)
    return (
        f"FIFA rank comparison favors {favored_team} by {rank_gap} places "
        f"({home_name}: {home_rank_value}, {away_name}: {away_rank_value})."
    )


def _normalize_form_list(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip().upper()
        return [normalized] if normalized else []
    if not isinstance(value, list):
        return []

    normalized_form: list[str] = []
    for item in value:
        normalized = str(item).strip().upper()
        if normalized:
            normalized_form.append(normalized)
    return normalized_form


def _build_research_messages(match_facts: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a football pre-match research assistant.\n"
                "Use the provided duckduckgo_search tool to gather current, factual information for one match.\n"
                "Prefer official federation, team, and mainstream sports media sources.\n"
                "Do not reference or use any historical prediction versions.\n"
                "When you have enough evidence, return only one valid JSON object.\n"
                "Do not output markdown."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": "research_match",
                    "match_facts": match_facts,
                    "requirements": [
                        "Use duckduckgo_search when external information is needed.",
                        "Generate a concise search plan and final structured research output.",
                        "Prioritize official and mainstream sources.",
                        "Capture concrete facts about recent form, injuries, lineups, venue context, and market sentiment when available.",
                        "Return all natural-language fields in English JSON strings only when needed for factual search summaries.",
                        "Keep the final output self-contained JSON.",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
        },
    ]


def _build_research_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "Search DuckDuckGo for up-to-date match research.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }
    ]


def _research_response_schema() -> dict[str, Any]:
    query_schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "query": {"type": "string"},
        },
        "required": ["topic", "query"],
        "additionalProperties": False,
    }
    document_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "title": {"type": "string"},
            "url": {"type": "string"},
            "domain": {"type": "string"},
            "source_tier": {"type": "string"},
            "published_at": {"type": ["string", "null"]},
            "fetched_at": {"type": "string"},
            "content_text": {"type": "string"},
            "content_hash": {"type": "string"},
        },
        "required": [
            "query",
            "title",
            "url",
            "domain",
            "source_tier",
            "published_at",
            "fetched_at",
            "content_text",
            "content_hash",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "search_plan": {
                "type": "object",
                "properties": {
                    "match_id": {"type": "string"},
                    "queries": {"type": "array", "items": query_schema},
                    "source_policy": {"type": "string"},
                },
                "required": ["match_id", "queries", "source_policy"],
                "additionalProperties": False,
            },
            "search_trace": {
                "type": "object",
                "properties": {
                    "completed": {"type": "boolean"},
                    "executed_queries": {"type": "array", "items": query_schema},
                    "opened_urls": {"type": "array", "items": {"type": "string"}},
                    "round_count": {"type": "integer"},
                },
                "required": ["completed", "executed_queries", "opened_urls", "round_count"],
                "additionalProperties": False,
            },
            "search_documents": {"type": "array", "items": document_schema},
            "used_fallback_sources": {"type": "boolean"},
        },
        "required": ["search_plan", "search_trace", "search_documents", "used_fallback_sources"],
        "additionalProperties": False,
    }


def _run_research_tool_loop(
    client: OpenRouterClient | Any,
    *,
    match_facts: dict[str, Any],
    timeout_seconds: float,
    plugins: list[dict[str, Any]],
    provider: dict[str, Any],
    search_tool: DuckDuckGoSearchTool | Any,
    max_tool_rounds: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    messages: list[dict[str, Any]] = list(_build_research_messages(match_facts))
    tool_trace = {
        "tool_name": "duckduckgo_search",
        "executed_queries": [],
        "opened_urls": [],
        "round_count": 0,
        "generated_from_match_facts": False,
        "search_documents": [],
    }

    while True:
        payload = _run_completion_with_timeout(
            client,
            timeout_seconds=timeout_seconds,
            messages=messages,
            response_format=None,
            plugins=plugins,
            provider=provider,
            tools=_build_research_tools(),
            tool_choice="auto",
        )
        message = _extract_first_message(payload)
        tool_calls = _extract_tool_calls(message)
        if not tool_calls:
            return payload, tool_trace

        if tool_trace["round_count"] >= max_tool_rounds:
            raise PredictionProviderResponseError("OpenRouter research tool loop exceeded max rounds.")

        tool_trace["round_count"] += 1
        messages.append(_assistant_message_for_history(message))

        for tool_call in tool_calls:
            tool_result = _execute_research_tool_call(
                tool_call,
                search_tool=search_tool,
                tool_trace=tool_trace,
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(tool_call.get("id") or ""),
                    "name": "duckduckgo_search",
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )


def _openrouter_plugins(enable_web_plugin: bool, enable_response_healing: bool) -> list[dict[str, Any]]:
    plugins: list[dict[str, Any]] = []
    if enable_web_plugin:
        plugins.append({"id": "web"})
    if enable_response_healing:
        plugins.append({"id": "response-healing"})
    return plugins


def _extract_first_message(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices") or []
    if not choices:
        raise PredictionProviderResponseError("OpenRouter research response did not include any choices.")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise PredictionProviderResponseError("OpenRouter research response did not include a valid message.")
    return message


def _extract_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list):
        return []
    return [tool_call for tool_call in tool_calls if isinstance(tool_call, dict)]


def _assistant_message_for_history(message: dict[str, Any]) -> dict[str, Any]:
    assistant_message: dict[str, Any] = {
        "role": "assistant",
        "content": message.get("content") or "",
    }
    tool_calls = _extract_tool_calls(message)
    if tool_calls:
        assistant_message["tool_calls"] = tool_calls
    return assistant_message


def _execute_research_tool_call(
    tool_call: dict[str, Any],
    *,
    search_tool: DuckDuckGoSearchTool | Any,
    tool_trace: dict[str, Any],
) -> dict[str, Any]:
    function_payload = tool_call.get("function")
    if not isinstance(function_payload, dict):
        raise PredictionProviderResponseError("OpenRouter research tool call payload was invalid.")

    function_name = str(function_payload.get("name") or "").strip()
    if function_name != "duckduckgo_search":
        raise PredictionProviderResponseError(
            f"OpenRouter research requested unsupported tool '{function_name or 'unknown'}'."
        )

    try:
        arguments = json.loads(str(function_payload.get("arguments") or "{}"))
    except json.JSONDecodeError as error:
        raise PredictionProviderResponseError("OpenRouter research tool arguments were not valid JSON.") from error

    if not isinstance(arguments, dict):
        raise PredictionProviderResponseError("OpenRouter research tool arguments were not valid JSON.")

    query = str(arguments.get("query") or "").strip()
    max_results = _normalize_int(arguments.get("max_results") or 5)
    tool_result = search_tool.search(query, max_results=max_results)
    search_results = tool_result.get("results") if isinstance(tool_result, dict) else None
    normalized_search_results = _normalize_tool_results(search_results)
    tool_trace["executed_queries"].append(
        {
            "query": query,
            "max_results": max_results,
            "result_count": len(normalized_search_results),
        }
    )
    tool_trace["opened_urls"].extend(result["url"] for result in normalized_search_results)
    tool_trace["search_documents"].extend(
        _build_tool_documents_from_results(query, normalized_search_results)
    )
    return {
        "results": normalized_search_results,
    }


def _extract_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise PredictionProviderResponseError("OpenRouter research response did not include any choices.")

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

    raise PredictionProviderResponseError("OpenRouter research response content was not parseable text.")


def _merge_tool_search_trace(
    base_trace: dict[str, Any],
    tool_trace: dict[str, Any],
) -> dict[str, Any]:
    return {
        **base_trace,
        "completed": True,
        "tool_name": tool_trace["tool_name"],
        "executed_queries": list(tool_trace["executed_queries"]),
        "opened_urls": list(tool_trace["opened_urls"]),
        "round_count": tool_trace["round_count"],
        "generated_from_match_facts": False,
    }


def _normalize_tool_results(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    normalized_results: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        domain = str(item.get("domain") or _domain_from_url(url)).strip()
        snippet = str(item.get("snippet") or "").strip()
        if not title or not url or not snippet:
            continue
        normalized_results.append(
            {
                "title": title,
                "url": url,
                "domain": domain or "unknown",
                "snippet": snippet,
            }
        )
    return normalized_results


def _build_tool_documents_from_results(
    query: str,
    search_results: list[dict[str, str]],
) -> list[dict[str, Any]]:
    fetched_at = datetime.now(UTC).isoformat()
    documents: list[dict[str, Any]] = []
    for result in search_results:
        documents.append(
            _build_document(
                query=query,
                title=result["title"],
                url=result["url"],
                domain=result["domain"],
                source_tier="search",
                fetched_at=fetched_at,
                content_text=result["snippet"],
            )
        )
    return documents


def _normalize_research_payload(match_id: str, raw_research: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_research, dict):
        raise PredictionProviderResponseError("OpenRouter research response must be a JSON object.")

    fetched_at = datetime.now(UTC).isoformat()
    search_plan = _coerce_dict(raw_research.get("search_plan"))
    search_plan["match_id"] = search_plan.get("match_id") or match_id
    search_plan["queries"] = _normalize_queries(search_plan.get("queries"))
    search_plan["source_policy"] = search_plan.get("source_policy") or "controlled-first"

    search_trace = _coerce_dict(raw_research.get("search_trace"))
    search_trace["completed"] = _normalize_bool(search_trace.get("completed"))
    search_trace["executed_queries"] = _normalize_queries(search_trace.get("executed_queries"))
    search_trace["opened_urls"] = _normalize_string_list(search_trace.get("opened_urls"))
    search_trace["round_count"] = _normalize_int(search_trace.get("round_count"))

    normalized_documents: list[dict[str, Any]] = []
    for document in _normalize_object_list(raw_research.get("search_documents")):
        content_text = str(document.get("content_text") or "").strip()
        url = str(document.get("url") or "").strip()
        normalized_documents.append(
            {
                "query": str(document.get("query") or "").strip(),
                "title": str(document.get("title") or "").strip(),
                "url": url,
                "domain": str(document.get("domain") or _domain_from_url(url)),
                "source_tier": str(document.get("source_tier") or "controlled"),
                "published_at": document.get("published_at"),
                "fetched_at": str(document.get("fetched_at") or fetched_at),
                "content_text": content_text,
                "content_hash": hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
            }
        )

    return {
        "search_plan": search_plan,
        "search_trace": search_trace,
        "search_documents": normalized_documents,
        "used_fallback_sources": _normalize_bool(raw_research.get("used_fallback_sources")),
    }


def _normalize_queries(value: Any) -> list[dict[str, str]]:
    queries: list[dict[str, str]] = []
    for item in _normalize_object_list(value):
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic") or "").strip()
        query = str(item.get("query") or "").strip()
        if topic and query:
            queries.append({"topic": topic, "query": query})
    return queries


def _domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or "unknown"


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
        raise PredictionProviderTimeoutError("OpenRouter research request timed out.")
    if captured_error:
        raise captured_error[0]
    return result["payload"]


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _normalize_object_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return []

    return [item for item in items if isinstance(item, dict)]


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if not isinstance(value, list):
        return []

    return [normalized for item in value if (normalized := str(item).strip())]


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _normalize_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
