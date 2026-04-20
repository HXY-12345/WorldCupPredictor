"""核心功能：基于 OpenRouter Chat Completions 实现真实比赛预测 provider。"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from backend.core.config import Settings
from backend.llm.openrouter import OpenRouterClient, OpenRouterSettings, load_openrouter_settings
from backend.llm.provider import (
    PredictionProvider,
    PredictionProviderConfigError,
    PredictionProviderResponseError,
    PredictionProviderTimeoutError,
    PredictionRequest,
)
from backend.services.prediction_schema import coerce_prediction_payload


class OpenRouterPredictionProvider(PredictionProvider):
    """使用 OpenRouter 大模型执行结构化预测。"""

    def __init__(
        self,
        settings: OpenRouterSettings,
        *,
        client: OpenRouterClient | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.settings = settings
        self.client = client or OpenRouterClient(settings, timeout_seconds=timeout_seconds)

    @classmethod
    def from_config(
        cls,
        model_config_path: str,
        key_path: str,
        *,
        timeout_seconds: float = 90.0,
    ) -> "OpenRouterPredictionProvider":
        try:
            settings = load_openrouter_settings(model_config_path, key_path)
        except ValueError as error:
            raise PredictionProviderConfigError(str(error)) from error
        return cls(settings, timeout_seconds=timeout_seconds)

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        try:
            payload = self.client.create_chat_completion(
                messages=request.messages,
                response_format=request.response_format,
                plugins=request.plugins,
                provider=request.provider,
            )
        except httpx.TimeoutException as error:
            raise PredictionProviderTimeoutError(f"OpenRouter prediction request timed out: {error}") from error
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response is not None else "unknown"
            response_text = error.response.text if error.response is not None else str(error)
            raise PredictionProviderResponseError(
                f"OpenRouter prediction request failed with status {status_code}: {response_text}"
            ) from error
        except httpx.HTTPError as error:
            raise PredictionProviderResponseError(f"OpenRouter prediction request failed: {error}") from error
        except json.JSONDecodeError as error:
            raise PredictionProviderResponseError("OpenRouter prediction response was not valid JSON.") from error

        completion_text = _extract_completion_text(payload)
        try:
            prediction = coerce_prediction_payload(completion_text)
        except ValueError as error:
            raise PredictionProviderResponseError("OpenRouter prediction response was not valid JSON.") from error

        if not isinstance(prediction, dict):
            raise PredictionProviderResponseError("OpenRouter prediction response must be a JSON object.")

        _fill_model_meta(prediction, payload, self.settings)
        _fill_input_snapshot(prediction, request)
        return prediction


def build_default_prediction_provider(settings: Settings) -> PredictionProvider | None:
    """根据应用配置构建默认真实预测 provider。"""

    model_config_path = settings.prediction_openrouter_model_config_path
    key_path = settings.prediction_openrouter_key_path

    if not model_config_path or not key_path:
        return None
    if not Path(model_config_path).exists() or not Path(key_path).exists():
        return None

    return OpenRouterPredictionProvider.from_config(
        model_config_path,
        key_path,
        timeout_seconds=settings.prediction_request_timeout_seconds,
    )


def _extract_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise PredictionProviderResponseError("OpenRouter prediction response did not include any choices.")

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

    raise PredictionProviderResponseError("OpenRouter prediction response content was not parseable text.")


def _fill_model_meta(
    prediction: dict[str, Any],
    payload: dict[str, Any],
    settings: OpenRouterSettings,
) -> None:
    model_meta = prediction.get("model_meta")
    if not isinstance(model_meta, dict):
        model_meta = {}
        prediction["model_meta"] = model_meta

    model_meta["provider"] = "openrouter"
    model_meta["model_name"] = payload.get("model") or settings.model
    model_meta.setdefault("predicted_at", datetime.now(UTC).isoformat())


def _fill_input_snapshot(prediction: dict[str, Any], request: PredictionRequest) -> None:
    request_match_facts = request.metadata.get("match_facts") if request.metadata else None
    if not isinstance(request_match_facts, dict):
        return

    input_snapshot = prediction.get("input_snapshot")
    if isinstance(input_snapshot, dict) and isinstance(input_snapshot.get("match_facts"), dict):
        input_snapshot = input_snapshot["match_facts"]

    if not isinstance(input_snapshot, dict):
        prediction["input_snapshot"] = dict(request_match_facts)
        return

    for key, value in request_match_facts.items():
        input_snapshot.setdefault(key, value)

    if "group_name" not in input_snapshot and "group" in request_match_facts:
        input_snapshot["group_name"] = request_match_facts["group"]

    prediction["input_snapshot"] = input_snapshot
