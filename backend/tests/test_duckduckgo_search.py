"""核心功能：验证本地 DuckDuckGo 搜索适配层的参数校验、结果裁剪与标准化输出。"""

import pytest

from backend.services.duckduckgo_search import DuckDuckGoSearchError, DuckDuckGoSearchTool


class DummyDDGS:
    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout
        self.calls: list[dict] = []

    def text(self, query: str, *, max_results: int, backend: str):
        self.calls.append(
            {
                "query": query,
                "max_results": max_results,
                "backend": backend,
            }
        )
        return [
            {
                "title": " Mexico vs South Africa preview ",
                "href": "https://example.com/preview",
                "body": " Mexico enters with steadier recent form. ",
            },
            {
                "title": "",
                "href": "",
                "body": "",
            },
        ]


def test_duckduckgo_search_tool_clamps_max_results_and_normalizes_results():
    created_clients: list[DummyDDGS] = []

    def factory(*, timeout: float | None = None):
        client = DummyDDGS(timeout=timeout)
        created_clients.append(client)
        return client

    tool = DuckDuckGoSearchTool(
        timeout_seconds=7.5,
        max_results_limit=5,
        ddgs_factory=factory,
    )

    payload = tool.search("  Mexico vs South Africa preview  ", max_results=99)

    assert created_clients[0].timeout == 7.5
    assert created_clients[0].calls == [
        {
            "query": "Mexico vs South Africa preview",
            "max_results": 5,
            "backend": "duckduckgo,mojeek",
        }
    ]
    assert payload == {
        "results": [
            {
                "title": "Mexico vs South Africa preview",
                "url": "https://example.com/preview",
                "domain": "example.com",
                "snippet": "Mexico enters with steadier recent form.",
            }
        ]
    }


def test_duckduckgo_search_tool_rejects_empty_query():
    tool = DuckDuckGoSearchTool(ddgs_factory=lambda **kwargs: DummyDDGS())

    with pytest.raises(DuckDuckGoSearchError) as exc_info:
        tool.search("   ", max_results=3)

    assert "query" in str(exc_info.value).lower()


def test_duckduckgo_search_tool_maps_upstream_errors():
    class ExplodingDDGS:
        def __init__(self, timeout: float | None = None) -> None:
            self.timeout = timeout

        def text(self, query: str, *, max_results: int, backend: str):
            raise RuntimeError("DDGS upstream exploded.")

    tool = DuckDuckGoSearchTool(ddgs_factory=lambda **kwargs: ExplodingDDGS())

    with pytest.raises(DuckDuckGoSearchError) as exc_info:
        tool.search("Mexico vs South Africa preview", max_results=3)

    assert "exploded" in str(exc_info.value).lower()


def test_duckduckgo_search_tool_treats_no_results_as_empty_payload():
    class NoResultsDDGS:
        def __init__(self, timeout: float | None = None) -> None:
            self.timeout = timeout

        def text(self, query: str, *, max_results: int, backend: str):
            raise RuntimeError("No results found.")

    tool = DuckDuckGoSearchTool(ddgs_factory=lambda **kwargs: NoResultsDDGS())

    payload = tool.search("Mexico vs South Africa preview", max_results=3)

    assert payload == {"results": []}
