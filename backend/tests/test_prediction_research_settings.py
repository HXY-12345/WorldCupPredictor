"""核心功能：验证 Research DuckDuckGo 工具链相关配置项具备稳定默认值。"""

from backend.core.config import Settings


def test_settings_expose_duckduckgo_research_tool_defaults():
    settings = Settings()

    assert settings.prediction_research_duckduckgo_enabled is True
    assert settings.prediction_research_duckduckgo_timeout_seconds == 5.0
    assert settings.prediction_research_duckduckgo_max_rounds == 4
    assert settings.prediction_research_duckduckgo_max_results_per_query == 5
    assert settings.prediction_research_duckduckgo_backend == "duckduckgo,mojeek"
