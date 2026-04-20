"""核心功能：验证预测 provider 接口与请求载体的基础契约。"""

from typing import Any

from backend.llm.provider import PredictionProvider, PredictionRequest


class DummyPredictionProvider:
    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        return {"status": "ok", "messages": len(request.messages)}


def test_prediction_provider_protocol_accepts_predict_implementations():
    assert isinstance(DummyPredictionProvider(), PredictionProvider)


def test_prediction_request_preserves_messages_and_schema_settings():
    request = PredictionRequest(
        messages=[{"role": "system", "content": "hello"}],
        response_format={"type": "json_schema"},
        plugins=[{"id": "web"}],
        provider={"require_parameters": True},
    )

    assert request.messages[0]["role"] == "system"
    assert request.response_format["type"] == "json_schema"
    assert request.plugins[0]["id"] == "web"
