"""
核心功能：实现首刷基线导入、增量 refresh、解析规范化与审计落库。

该模块负责从 FIFA 官方数据源获取比赛信息，通过 LLM 解析结构化数据，
并将结果规范化后存入数据库。支持两种刷新模式：
- baseline: 首次全量导入，输出完整赛程
- incremental: 增量更新，仅输出有变化的比赛
"""

import json
import re
import inspect
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterClient, load_openrouter_settings
from backend.models.match import Match
import httpx
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterClient, load_openrouter_settings
from backend.models.match import Match
from backend.models.parse_output import ParseOutput
from backend.models.source_snapshot import SourceSnapshot
from backend.models.sync_run import SyncRun
from backend.repositories.matches import MatchRepository
from backend.evaluation.service import evaluate_finished_matches
from backend.services.seed import seed_matches_from_fixture

# 最大源文本字符数限制，防止 LLM 输入过长
MAX_SOURCE_TEXT_CHARS = 12000


@dataclass(frozen=True)
class FetchedSource:
    """抓取的数据源信息。

    Attributes:
        source_name: 数据源名称（如 "fifa_article"）
        source_url: 数据源 URL
        content_type: HTTP 响应的 Content-Type
        raw_body: 原始响应内容（可能被截断）
        extracted_text: 从内容中提取的文本（HTML 会转为纯文本）
    """
    source_name: str
    source_url: str
    content_type: str | None
    raw_body: str
    extracted_text: str | None = None


class RefreshFetcher(Protocol):
    """数据源抓取器协议。

    实现 fetch 方法从外部数据源获取原始数据。
    """

    def fetch(self) -> list[FetchedSource]:
        """抓取所有配置的数据源，返回抓取结果列表。"""
        ...


class RefreshParser(Protocol):
    """数据解析器协议。

    实现 parse 方法将抓取的原始数据解析为结构化的比赛信息。
    """

    def parse(self, sources: list[FetchedSource]) -> dict[str, Any]:
        """解析数据源，返回结构化的比赛数据。"""
        ...


@dataclass
class RefreshPipeline:
    """刷新流水线，组合抓取器和解析器。"""
    fetcher: RefreshFetcher
    parser: RefreshParser


@dataclass(frozen=True)
class RefreshContext:
    """刷新执行的上下文信息。

    Attributes:
        mode: 刷新模式（"baseline" 或 "incremental"）
        existing_match_count: 数据库中现有比赛数量
        fixture_bootstrapped: 是否已从 fixture 文件预加载
    """
    mode: str
    existing_match_count: int
    fixture_bootstrapped: bool = False


@dataclass(frozen=True)
class SourceSpec:
    """数据源配置规范。

    Attributes:
        source_name: 数据源标识名称
        source_url: 数据源 URL 地址
    """
    source_name: str
    source_url: str


class FifaOfficialFetcher:
    """FIFA 官方数据源抓取器。

    从 FIFA 官方网站抓取比赛数据，支持 HTML 和纯文本格式。
    """

    def __init__(self, source_specs: list[SourceSpec], *, timeout_seconds: float = 30.0) -> None:
        """初始化抓取器。

        Args:
            source_specs: 要抓取的数据源列表
            timeout_seconds: 请求超时时间（秒）
        """
        self.source_specs = source_specs
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> list[FetchedSource]:
        """抓取所有配置的数据源。

        Returns:
            抓取成功的数据源列表

        Raises:
            RuntimeError: 所有数据源都抓取失败时抛出
        """
        fetched_sources: list[FetchedSource] = []
        failures: list[str] = []

        headers = {
            "User-Agent": "WorldCup Predictor/1.0",
            "Accept": "*/*",
        }

        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            for source_spec in self.source_specs:
                try:
                    response = client.get(source_spec.source_url, headers=headers)
                    response.raise_for_status()
                    raw_body, extracted_text = _extract_source_content(response)
                    fetched_sources.append(
                        FetchedSource(
                            source_name=source_spec.source_name,
                            source_url=source_spec.source_url,
                            content_type=response.headers.get("content-type"),
                            raw_body=raw_body,
                            extracted_text=extracted_text,
                        )
                    )
                except Exception as error:
                    failures.append(f"{source_spec.source_name}: {error}")

        if fetched_sources:
            return fetched_sources

        raise RuntimeError(f"Unable to fetch FIFA official sources. {'; '.join(failures)}")


class OpenRouterScheduleParser:
    """基于 OpenRouter LLM 的赛程解析器。

    使用大语言模型从非结构化数据源中提取结构化的比赛信息。
    """

    def __init__(
        self,
        *,
        model_config_path: str,
        key_path: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        """初始化解析器。

        Args:
            model_config_path: OpenRouter 模型配置文件路径
            key_path: OpenRouter API 密钥文件路径
            timeout_seconds: API 请求超时时间（秒）
        """
        self.settings = load_openrouter_settings(model_config_path, key_path)
        self.client = OpenRouterClient(self.settings, timeout_seconds=timeout_seconds)

    def parse(self, sources: list[FetchedSource], context: RefreshContext | None = None) -> dict[str, Any]:
        """解析数据源，提取结构化赛程信息。

        Args:
            sources: 抓取的数据源列表
            context: 刷新上下文，用于确定解析模式

        Returns:
            包含以下键的字典：
            - model_name: 使用的模型名称
            - parser_version: 解析器版本
            - structured_data: 解析出的结构化比赛数据
            - raw_response: 原始 API 响应
        """
        refresh_mode = context.mode if context else "baseline"
        payload = self.client.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract the FIFA World Cup 2026 official match schedule. "
                        "Prefer FIFA official sources. If official source text is incomplete or unavailable, "
                        "you may use web search to fill gaps, but keep FIFA as the primary reference whenever possible. "
                        "Return only JSON that matches the provided schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Build a structured schedule payload for the frontend and database.\n"
                        "Requirements:\n"
                        f"- Current refresh mode is: {refresh_mode}.\n"
                        "- Use match ids like fwc2026-m001, fwc2026-m002, etc.\n"
                        "- Use ISO dates in YYYY-MM-DD.\n"
                        "- Use status values such as not_started, in_progress, finished.\n"
                        "- Keep placeholder participants such as Winner Group A when official teams are not confirmed yet.\n"
                        "- Focus on the latest official facts: confirmed teams, kickoff corrections, venue corrections, match status, and final score.\n"
                        "- Keep prediction null. Only include score when the official source clearly contains it.\n"
                        "- Set last_updated to an ISO timestamp.\n"
                        "- If an official page is unavailable, you may use web search to recover the schedule.\n\n"
                        f"{_build_mode_requirements(refresh_mode)}\n\n"
                        f"Sources:\n{json.dumps(_serialize_sources(sources), ensure_ascii=False)}"
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "worldcup_schedule_payload",
                    "strict": True,
                    "schema": _schedule_response_schema(),
                },
            },
            plugins=_openrouter_plugins(self.settings.enable_web_plugin, self.settings.enable_response_healing),
            provider={"require_parameters": self.settings.require_parameters},
        )

        completion_text = _extract_completion_text(payload)
        structured_data = json.loads(completion_text)

        return {
            "model_name": payload.get("model") or self.settings.model,
            "parser_version": "openrouter-chat-completions-v1",
            "structured_data": structured_data,
            "raw_response": payload,
        }


def run_refresh(
    session_factory: sessionmaker[Session],
    fixture_seed_path: str | None,
    refresh_pipeline: RefreshPipeline | None = None,
) -> SyncRun:
    """执行数据刷新流程。

    这是刷新功能的主入口，负责：
    1. 创建同步运行记录
    2. 根据数据状态选择刷新策略
    3. 抓取、解析、规范化数据
    4. 落库并更新同步记录状态

    Args:
        session_factory: 数据库会话工厂
        fixture_seed_path: fixture 种子数据文件路径（可选）
        refresh_pipeline: 刷新流水线（为 None 时仅使用 fixture）

    Returns:
        同步运行记录，包含执行状态和结果
    """
    sync_run_id = uuid4().hex
    started_at = datetime.now(UTC).isoformat()

    with session_factory() as session:
        sync_run = SyncRun(
            id=sync_run_id,
            trigger_type="manual",
            status="running",
            started_at=started_at,
            finished_at=None,
            source_name=None,
            error_message=None,
        )
        session.add(sync_run)
        session.commit()

    source_name: str | None = None
    error_message: str | None = None
    status = "completed"
    existing_match_count = _count_matches(session_factory)
    is_baseline_refresh = existing_match_count == 0
    fixture_bootstrapped = False

    try:
        if refresh_pipeline is None:
            seed_matches_from_fixture(session_factory, fixture_seed_path)
            evaluate_finished_matches(session_factory)
            source_name = "fixture-seed"
        else:
            if is_baseline_refresh and fixture_seed_path:
                seed_matches_from_fixture(session_factory, fixture_seed_path)
                fixture_bootstrapped = True
            sources = refresh_pipeline.fetcher.fetch()
            parse_result = _parse_with_context(
                refresh_pipeline.parser,
                sources,
                RefreshContext(
                    mode="baseline" if is_baseline_refresh else "incremental",
                    existing_match_count=existing_match_count,
                    fixture_bootstrapped=fixture_bootstrapped,
                ),
            )
            structured_data = parse_result["structured_data"]
            source_name = _resolve_source_name(sources)

            with session_factory() as session:
                normalized_data = _normalize_structured_data(session, structured_data)
                session.add_all(
                    [
                        SourceSnapshot(
                            sync_run_id=sync_run_id,
                            source_name=source.source_name,
                            source_url=source.source_url,
                            content_type=source.content_type,
                            raw_body=source.raw_body,
                            extracted_text=source.extracted_text,
                        )
                        for source in sources
                    ]
                )
                session.add(
                    ParseOutput(
                        sync_run_id=sync_run_id,
                        model_name=parse_result["model_name"],
                        parser_version=parse_result["parser_version"],
                        structured_data=normalized_data,
                        raw_response=_stringify_raw_response(parse_result.get("raw_response")),
                    )
                )
                repository = MatchRepository(session)
                repository.upsert_many(normalized_data, sync_run_id=sync_run_id)
            evaluate_finished_matches(session_factory)

    except Exception as error:
        status = "failed"
        error_message = str(error)

    finished_at = datetime.now(UTC).isoformat()

    with session_factory() as session:
        sync_run = session.get(SyncRun, sync_run_id)
        sync_run.status = status
        sync_run.finished_at = finished_at
        sync_run.source_name = source_name
        sync_run.error_message = error_message
        session.add(sync_run)
        session.commit()
        session.refresh(sync_run)
        return sync_run


def build_default_refresh_pipeline(settings: Settings) -> RefreshPipeline | None:
    """构建默认的刷新流水线。

    根据配置创建 FIFA 官方数据源抓取器和 OpenRouter 解析器。

    Args:
        settings: 应用配置对象

    Returns:
        配置好的刷新流水线，如果配置缺失则返回 None
    """
    model_config_path = settings.openrouter_model_config_path
    key_path = settings.openrouter_key_path

    if not model_config_path or not key_path:
        return None

    if not Path(model_config_path).exists() or not Path(key_path).exists():
        return None

    return RefreshPipeline(
        fetcher=FifaOfficialFetcher(
            [
                SourceSpec("fifa_article", settings.fifa_article_url),
                SourceSpec("fifa_schedule_pdf", settings.fifa_schedule_pdf_url),
            ],
            timeout_seconds=settings.refresh_request_timeout_seconds,
        ),
        parser=OpenRouterScheduleParser(
            model_config_path=model_config_path,
            key_path=key_path,
            timeout_seconds=settings.refresh_request_timeout_seconds,
        ),
    )


def _extract_source_content(response: httpx.Response) -> tuple[str, str | None]:
    """从 HTTP 响应中提取内容。

    根据 Content-Type 处理不同格式的响应：
    - HTML: 提取纯文本
    - JSON/XML/Text: 直接返回
    - 其他: 返回占位符

    Args:
        response: HTTP 响应对象

    Returns:
        (原始内容, 提取的文本) 元组
    """
    content_type = (response.headers.get("content-type") or "").lower()

    if "html" in content_type:
        raw_body = _truncate_text(response.text)
        return raw_body, _truncate_text(_html_to_text(response.text))

    if any(text_content_type in content_type for text_content_type in ("json", "xml", "text", "javascript")):
        raw_body = _truncate_text(response.text)
        return raw_body, raw_body

    return f"[binary content omitted: {len(response.content)} bytes]", None


def _serialize_sources(sources: list[FetchedSource]) -> list[dict[str, Any]]:
    """将数据源序列化为字典列表，用于发送给 LLM。

    Args:
        sources: 数据源列表

    Returns:
        包含数据源摘要信息的字典列表
    """
    return [
        {
            "source_name": source.source_name,
            "source_url": source.source_url,
            "content_type": source.content_type,
            "raw_body_excerpt": _truncate_text(source.raw_body),
            "extracted_text_excerpt": _truncate_text(source.extracted_text or ""),
        }
        for source in sources
    ]


def _extract_completion_text(payload: dict[str, Any]) -> str:
    """从 OpenRouter API 响应中提取完成文本。

    Args:
        payload: OpenRouter API 响应载荷

    Returns:
        提取的文本内容

    Raises:
        ValueError: 响应格式无法解析时抛出
    """
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("OpenRouter response did not include any choices.")

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

    raise ValueError("OpenRouter response content was not parseable text.")


def _resolve_source_name(sources: list[FetchedSource]) -> str:
    """解析数据源名称。

    单个数据源直接返回名称，多个数据源用逗号连接。

    Args:
        sources: 数据源列表

    Returns:
        数据源名称字符串
    """
    if len(sources) == 1:
        return sources[0].source_name
    return ",".join(source.source_name for source in sources)[:64]


def _stringify_raw_response(raw_response: Any) -> str | None:
    """将原始响应转换为字符串。

    Args:
        raw_response: 原始响应（可能是 None、字符串或字典）

    Returns:
        字符串形式的响应，或 None
    """
    if raw_response is None:
        return None
    if isinstance(raw_response, str):
        return raw_response
    return json.dumps(raw_response, ensure_ascii=False)


def _truncate_text(value: str, limit: int = MAX_SOURCE_TEXT_CHARS) -> str:
    """截断文本到指定长度。

    Args:
        value: 原始文本
        limit: 最大字符数限制

    Returns:
        截断后的文本（如果未超过长度则原样返回）
    """
    if len(value) <= limit:
        return value
    return value[:limit]


def _html_to_text(html_text: str) -> str:
    """将 HTML 转换为纯文本。

    移除 script/style 标签和所有 HTML 标签，规范化空白字符。

    Args:
        html_text: HTML 文本

    Returns:
        提取的纯文本
    """
    without_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    normalized = re.sub(r"\s+", " ", unescape(without_tags))
    return normalized.strip()


def _openrouter_plugins(enable_web_plugin: bool, enable_response_healing: bool) -> list[dict[str, Any]]:
    """构建 OpenRouter 插件配置。

    Args:
        enable_web_plugin: 是否启用网络搜索插件
        enable_response_healing: 是否启用响应修复插件

    Returns:
        插件配置列表
    """
    plugins: list[dict[str, Any]] = []
    if enable_web_plugin:
        plugins.append({"id": "web"})
    if enable_response_healing:
        plugins.append({"id": "response-healing"})
    return plugins


def _schedule_response_schema() -> dict[str, Any]:
    """构建 LLM 响应的 JSON Schema。

    定义了比赛数据的结构化格式，包括球队、比赛、比分等字段。

    Returns:
        JSON Schema 字典
    """
    nullable_string = {"type": ["string", "null"]}
    nullable_integer = {"type": ["integer", "null"]}
    nullable_object = {"type": ["object", "null"], "additionalProperties": True}

    team_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "flag": nullable_string,
            "fifa_rank": nullable_integer,
            "form": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "flag", "fifa_rank", "form"],
        "additionalProperties": False,
    }

    match_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "official_match_number": nullable_integer,
            "kickoff_label": nullable_string,
            "sort_order": {"type": "integer"},
            "date": {"type": "string"},
            "time": nullable_string,
            "stage": nullable_string,
            "group": nullable_string,
            "venue": nullable_string,
            "home_team": team_schema,
            "away_team": team_schema,
            "status": nullable_string,
            "score": nullable_object,
            "prediction": nullable_object,
            "head_to_head": nullable_object,
            "key_players": nullable_object,
        },
        "required": [
            "id",
            "official_match_number",
            "kickoff_label",
            "sort_order",
            "date",
            "time",
            "stage",
            "group",
            "venue",
            "home_team",
            "away_team",
            "status",
            "score",
            "prediction",
            "head_to_head",
            "key_players",
        ],
        "additionalProperties": False,
    }

    return {
        "type": "object",
        "properties": {
            "matches": {"type": "array", "items": match_schema},
            "last_updated": {"type": "string"},
            "total": {"type": "integer"},
        },
        "required": ["matches", "last_updated", "total"],
        "additionalProperties": False,
    }


def _count_matches(session_factory: sessionmaker[Session]) -> int:
    """统计数据库中的比赛数量。

    Args:
        session_factory: 数据库会话工厂

    Returns:
        现有比赛数量
    """
    with session_factory() as session:
        repository = MatchRepository(session)
        return repository.count()


def _parse_with_context(
    parser: RefreshParser,
    sources: list[FetchedSource],
    context: RefreshContext,
) -> dict[str, Any]:
    """根据解析器签名选择合适的调用方式。

    检查解析器的 parse 方法是否接受 context 参数，
    兼容不同版本的解析器接口。

    Args:
        parser: 解析器实例
        sources: 数据源列表
        context: 刷新上下文

    Returns:
        解析结果字典
    """
    parse_method = getattr(parser, "parse")
    parameters = list(inspect.signature(parse_method).parameters.values())
    if len(parameters) >= 2:
        return parse_method(sources, context)
    return parse_method(sources)


def _build_mode_requirements(refresh_mode: str) -> str:
    """根据刷新模式构建 LLM prompt 要求。

    Args:
        refresh_mode: 刷新模式（"baseline" 或 "incremental"）

    Returns:
        模式特定的 prompt 要求文本
    """
    if refresh_mode == "incremental":
        return (
            "- Output only matches that have newly confirmed or corrected official facts.\n"
            "- Do not re-output unchanged matches just to mirror the full schedule.\n"
            "- Pay extra attention to participant confirmations, kickoff corrections, venue corrections, status changes, and score changes.\n"
            "- Set total to the number of matches included in this incremental payload."
        )

    return (
        "- Output the full official schedule baseline under matches[].\n"
        "- Include all known matches, even if some participants are still placeholders.\n"
        "- Set total to the full number of matches included in the baseline payload."
    )


def _normalize_structured_data(session: Session, structured_data: dict[str, Any]) -> dict[str, Any]:
    """规范化结构化数据。

    对每场比赛数据进行规范化处理，确保数据格式一致。
    同时更新 last_updated 时间戳。

    Args:
        session: 数据库会话
        structured_data: LLM 解析出的原始数据

    Returns:
        规范化后的数据字典
    """
    normalized_matches = [
        _normalize_match_payload(session, match_payload)
        for match_payload in structured_data.get("matches", [])
    ]
    return {
        "matches": normalized_matches,
        "last_updated": structured_data.get("last_updated") or datetime.now(UTC).isoformat(),
        "total": len(normalized_matches),
    }


def _normalize_match_payload(session: Session, match_payload: dict[str, Any]) -> dict[str, Any]:
    """规范化单场比赛数据。

    将 LLM 解析的数据与数据库中现有数据合并，
    优先使用新数据，缺失字段回退到旧数据。

    Args:
        session: 数据库会话
        match_payload: LLM 解析的比赛数据

    Returns:
        规范化后的比赛数据字典
    """
    match_id = _resolve_match_id(match_payload)
    existing_match = session.get(Match, match_id) if match_id else None
    existing_payload = _serialize_existing_match(existing_match) if existing_match else {}

    return {
        "id": match_id,
        "official_match_number": match_payload.get("official_match_number", existing_payload.get("official_match_number")),
        "kickoff_label": match_payload.get("kickoff_label", existing_payload.get("kickoff_label")),
        "sort_order": match_payload.get("sort_order", existing_payload.get("sort_order", 0)),
        "date": match_payload.get("date", existing_payload.get("date")),
        "time": match_payload.get("time", existing_payload.get("time")),
        "stage": match_payload.get("stage", existing_payload.get("stage")),
        "group": _normalize_group_value(match_payload.get("group", existing_payload.get("group"))),
        "venue": match_payload.get("venue", existing_payload.get("venue")),
        "home_team": _normalize_team_payload(match_payload.get("home_team"), existing_payload.get("home_team")),
        "away_team": _normalize_team_payload(match_payload.get("away_team"), existing_payload.get("away_team")),
        "status": match_payload.get("status", existing_payload.get("status")),
        "score": deepcopy(match_payload.get("score", existing_payload.get("score"))),
        "prediction": deepcopy(match_payload.get("prediction", existing_payload.get("prediction"))),
        "head_to_head": deepcopy(match_payload.get("head_to_head", existing_payload.get("head_to_head"))),
        "key_players": _normalize_key_players(match_payload.get("key_players"), existing_payload.get("key_players")),
    }


def _resolve_match_id(match_payload: dict[str, Any]) -> str:
    """从比赛载荷中解析出比赛 ID。

    按优先级尝试以下字段：
    1. id
    2. match_id
    3. official_match_number（生成格式：fwc2026-m001）
    4. kickoff_label 中的数字

    Args:
        match_payload: 比赛数据字典

    Returns:
        比赛唯一标识符

    Raises:
        ValueError: 无法解析出有效的比赛 ID
    """
    match_id = match_payload.get("id") or match_payload.get("match_id")
    if isinstance(match_id, str) and match_id.strip():
        return match_id.strip()

    official_match_number = match_payload.get("official_match_number")
    if isinstance(official_match_number, int):
        return f"fwc2026-m{official_match_number:03d}"

    kickoff_label = match_payload.get("kickoff_label")
    if isinstance(kickoff_label, str):
        digits = "".join(character for character in kickoff_label if character.isdigit())
        if digits:
            return f"fwc2026-m{int(digits):03d}"

    raise ValueError("Refresh parse output missing match identifier.")


def _serialize_existing_match(match: Match) -> dict[str, Any]:
    """将数据库中的比赛对象序列化为字典。

    用于与新数据合并时提供回退值。

    Args:
        match: 比赛模型实例

    Returns:
        比赛数据字典
    """
    return {
        "id": match.id,
        "official_match_number": match.official_match_number,
        "kickoff_label": match.kickoff_label,
        "sort_order": match.sort_order,
        "date": match.date,
        "time": match.time,
        "stage": match.stage,
        "group": match.group_name,
        "venue": match.venue,
        "home_team": deepcopy(match.home_team),
        "away_team": deepcopy(match.away_team),
        "status": match.status,
        "score": deepcopy(match.score),
        "prediction": deepcopy(match.prediction),
        "head_to_head": deepcopy(match.head_to_head),
        "key_players": deepcopy(match.key_players),
    }


def _normalize_team_payload(incoming_team: Any, existing_team: Any) -> dict[str, Any]:
    """规范化球队数据。

    将新球队数据与现有数据合并，支持字符串和字典两种输入格式。

    Args:
        incoming_team: 新的球队数据（字符串或字典）
        existing_team: 现有的球队数据字典

    Returns:
        规范化后的球队数据字典
    """
    baseline = deepcopy(existing_team) if isinstance(existing_team, dict) else {}
    normalized = {
        "name": baseline.get("name"),
        "flag": baseline.get("flag"),
        "fifa_rank": baseline.get("fifa_rank"),
        "form": deepcopy(baseline.get("form") or []),
    }

    if isinstance(incoming_team, str):
        normalized["name"] = incoming_team
        return normalized

    if isinstance(incoming_team, dict):
        normalized["name"] = incoming_team.get("name", normalized.get("name"))
        normalized["flag"] = incoming_team.get("flag", normalized.get("flag"))
        normalized["fifa_rank"] = incoming_team.get("fifa_rank", normalized.get("fifa_rank"))
        normalized["form"] = deepcopy(incoming_team.get("form", normalized.get("form") or []))
        return normalized

    return normalized


def _normalize_key_players(incoming_value: Any, existing_value: Any) -> dict[str, Any] | None:
    """规范化关键球员数据。

    Args:
        incoming_value: 新的关键球员数据
        existing_value: 现有的关键球员数据

    Returns:
        规范化后的关键球员数据，或 None
    """
    if isinstance(incoming_value, dict):
        return deepcopy(incoming_value)
    if isinstance(existing_value, dict):
        return deepcopy(existing_value)
    return None


def _normalize_group_value(group_value: Any) -> Any:
    """规范化小组名称。

    将 "Group A" 格式统一为单个大写字母 "A"。

    Args:
        group_value: 原始小组名称

    Returns:
        规范化后的小组名称（单个大写字母）
    """
    if not isinstance(group_value, str):
        return group_value
    normalized = group_value.strip()
    match = re.fullmatch(r"Group\s+([A-Z])", normalized, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return normalized
