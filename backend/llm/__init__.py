"""核心功能：暴露大模型接入层的公开接口与配置加载函数。"""

from backend.llm.openrouter import OpenRouterClient, OpenRouterSettings, load_openrouter_settings

__all__ = ["OpenRouterClient", "OpenRouterSettings", "load_openrouter_settings"]
