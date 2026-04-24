"""核心功能：封装 Research 阶段可复用的本地 DuckDuckGo 搜索工具。"""

from typing import Any, Callable
from urllib.parse import urlparse


class DuckDuckGoSearchError(Exception):
    """DuckDuckGo 搜索工具执行失败时抛出的统一异常。"""


class DuckDuckGoSearchTool:
    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        max_results_limit: int = 5,
        ddgs_factory: Callable[..., Any] | None = None,
        backend: str = "duckduckgo,mojeek",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_results_limit = max_results_limit
        self.ddgs_factory = ddgs_factory or _default_ddgs_factory
        self.backend = backend

    def search(self, query: str, *, max_results: int) -> dict[str, list[dict[str, str]]]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            raise DuckDuckGoSearchError("DuckDuckGo search query must not be empty.")

        normalized_max_results = _clamp_max_results(max_results, self.max_results_limit)

        try:
            client = _build_ddgs_client(
                self.ddgs_factory,
                timeout_seconds=self.timeout_seconds,
            )
            raw_results = client.text(
                normalized_query,
                max_results=normalized_max_results,
                backend=self.backend,
            )
        except DuckDuckGoSearchError:
            raise
        except Exception as error:
            if _is_no_results_error(error):
                return {"results": []}
            raise DuckDuckGoSearchError(f"DuckDuckGo search failed: {error}") from error

        return {
            "results": _normalize_results(raw_results),
        }


def _default_ddgs_factory(**kwargs: Any) -> Any:
    try:
        from ddgs import DDGS
    except ImportError as error:
        raise DuckDuckGoSearchError(
            "DuckDuckGo search dependency is not installed. Install 'ddgs' first."
        ) from error

    return DDGS(**kwargs)


def _build_ddgs_client(factory: Callable[..., Any], *, timeout_seconds: float) -> Any:
    try:
        return factory(timeout=timeout_seconds)
    except TypeError:
        return factory()


def _clamp_max_results(value: int, limit: int) -> int:
    normalized_limit = max(int(limit or 1), 1)
    try:
        normalized_value = int(value or 1)
    except (TypeError, ValueError):
        normalized_value = 1
    return min(max(normalized_value, 1), normalized_limit)


def _normalize_results(raw_results: Any) -> list[dict[str, str]]:
    normalized_results: list[dict[str, str]] = []

    if raw_results is None:
        return normalized_results

    if isinstance(raw_results, dict):
        items = [raw_results]
    else:
        items = list(raw_results)

    for item in items:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or "").strip()
        url = str(item.get("href") or item.get("url") or "").strip()
        snippet = str(item.get("body") or item.get("snippet") or "").strip()
        if not title or not url or not snippet:
            continue

        normalized_results.append(
            {
                "title": title,
                "url": url,
                "domain": _domain_from_url(url),
                "snippet": snippet,
            }
        )

    return normalized_results


def _domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or "unknown"


def _is_no_results_error(error: Exception) -> bool:
    return "no results found" in str(error).strip().lower()
