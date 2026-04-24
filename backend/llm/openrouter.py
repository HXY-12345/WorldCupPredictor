"""核心功能：封装 OpenRouter 配置读取与 Chat Completions 调用，并兼容尾随噪声响应。"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from backend.services.structured_output import extract_json_object_text


@dataclass(frozen=True)
class OpenRouterSettings:
    base_url: str
    model: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 4000
    http_referer: str | None = None
    x_title: str | None = None
    enable_web_plugin: bool = True
    enable_response_healing: bool = True
    require_parameters: bool = True


def load_openrouter_settings(model_config_path: str, key_path: str) -> OpenRouterSettings:
    model_payload = json.loads(Path(model_config_path).read_text(encoding="utf-8"))
    api_key = Path(key_path).read_text(encoding="utf-8").strip()

    if not api_key:
        raise ValueError("OpenRouter API key file is empty.")

    return OpenRouterSettings(
        base_url=model_payload["base_url"],
        model=model_payload["model"],
        api_key=api_key,
        temperature=float(model_payload.get("temperature", 0.1)),
        max_tokens=int(model_payload.get("max_tokens", 4000)),
        http_referer=model_payload.get("http_referer"),
        x_title=model_payload.get("x_title"),
        enable_web_plugin=bool(model_payload.get("enable_web_plugin", True)),
        enable_response_healing=bool(model_payload.get("enable_response_healing", True)),
        require_parameters=bool(model_payload.get("require_parameters", True)),
    )


class OpenRouterClient:
    def __init__(self, settings: OpenRouterSettings, *, timeout_seconds: float = 120.0) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds

    def create_chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any] | None = None,
        plugins: list[dict[str, Any]] | None = None,
        provider: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        if self.settings.http_referer:
            headers["HTTP-Referer"] = self.settings.http_referer
        if self.settings.x_title:
            headers["X-OpenRouter-Title"] = self.settings.x_title

        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if plugins:
            payload["plugins"] = plugins
        if provider:
            payload["provider"] = provider
        if tools:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = parallel_tool_calls

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(self.settings.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return _load_response_payload(response)


def _load_response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        try:
            payload = json.loads(extract_json_object_text(response.text))
        except ValueError as error:
            raise json.JSONDecodeError("OpenRouter response body was empty.", response.text, 0) from error

    if not isinstance(payload, dict):
        raise json.JSONDecodeError("OpenRouter response was not a JSON object.", response.text, 0)
    return payload
