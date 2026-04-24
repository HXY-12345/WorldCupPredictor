"""核心功能：验证 OpenRouter HTTP 客户端的响应容错与 tool-calling 请求透传行为。"""

import json

import httpx
import pytest

from backend.llm.openrouter import OpenRouterClient, OpenRouterSettings


def _settings() -> OpenRouterSettings:
    return OpenRouterSettings(
        base_url="https://openrouter.ai/api/v1/chat/completions",
        model="qwen/qwen3.5-flash-20260224",
        api_key="sk-or-v1-test-key",
    )


class DummyHttpxClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url: str, *, headers: dict | None = None, json: dict | None = None) -> httpx.Response:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
            }
        )
        return self.response


def test_openrouter_client_recovers_when_response_json_has_trailing_noise(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "model": "qwen/qwen3.5-flash-20260224",
        "choices": [
            {
                "message": {
                    "content": "{\"ok\":true}",
                }
            }
        ],
    }
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("POST", _settings().base_url),
        content=(json.dumps(payload, ensure_ascii=False) + "\n\nrequest id: abc123").encode("utf-8"),
    )
    dummy_client = DummyHttpxClient(response)
    monkeypatch.setattr("backend.llm.openrouter.httpx.Client", lambda timeout: dummy_client)

    client = OpenRouterClient(_settings())

    result = client.create_chat_completion(
        messages=[{"role": "user", "content": "hello"}],
        response_format=None,
        plugins=None,
        provider=None,
    )

    assert result["model"] == "qwen/qwen3.5-flash-20260224"
    assert dummy_client.calls[0]["json"]["model"] == "qwen/qwen3.5-flash-20260224"


def test_openrouter_client_forwards_tool_calling_fields(monkeypatch: pytest.MonkeyPatch):
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("POST", _settings().base_url),
        json={"id": "chatcmpl_test", "choices": []},
    )
    dummy_client = DummyHttpxClient(response)
    monkeypatch.setattr("backend.llm.openrouter.httpx.Client", lambda timeout: dummy_client)

    client = OpenRouterClient(_settings())
    tools = [
        {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "Search DuckDuckGo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    client.create_chat_completion(
        messages=[{"role": "user", "content": "search"}],
        response_format=None,
        plugins=None,
        provider=None,
        tools=tools,
        tool_choice="auto",
        parallel_tool_calls=False,
    )

    sent_payload = dummy_client.calls[0]["json"]
    assert sent_payload["tools"] == tools
    assert sent_payload["tool_choice"] == "auto"
    assert sent_payload["parallel_tool_calls"] is False


def test_openrouter_client_raises_json_decode_error_when_response_body_is_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("POST", _settings().base_url),
        content=b"",
    )
    dummy_client = DummyHttpxClient(response)
    monkeypatch.setattr("backend.llm.openrouter.httpx.Client", lambda timeout: dummy_client)

    client = OpenRouterClient(_settings())

    with pytest.raises(json.JSONDecodeError):
        client.create_chat_completion(
            messages=[{"role": "user", "content": "hello"}],
            response_format=None,
            plugins=None,
            provider=None,
        )
