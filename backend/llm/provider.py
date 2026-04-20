"""核心功能：定义预测智能体的请求载体、统一接口与基础异常类型。"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class PredictionProviderError(RuntimeError):
    """预测 provider 的基础异常。"""


class PredictionProviderConfigError(PredictionProviderError):
    """预测 provider 配置错误。"""


class PredictionProviderResponseError(PredictionProviderError):
    """预测 provider 响应解析错误。"""


class PredictionProviderTimeoutError(PredictionProviderError):
    """预测 provider 请求超时错误。"""


@dataclass(frozen=True)
class PredictionRequest:
    """预测请求载体。"""

    messages: list[dict[str, Any]]
    response_format: dict[str, Any] | None = None
    plugins: list[dict[str, Any]] = field(default_factory=list)
    provider: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@runtime_checkable
class PredictionProvider(Protocol):
    """预测 provider 统一接口。"""

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        """根据请求返回原始预测响应。"""

