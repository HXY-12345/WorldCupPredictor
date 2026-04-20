"""核心功能：验证 OpenRouter 模型配置与密钥文件可被分离加载。"""

import json
from pathlib import Path
from uuid import uuid4

from backend.llm.openrouter import load_openrouter_settings


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def test_load_openrouter_settings_reads_model_and_key_from_separate_files():
    runtime_dir = _runtime_dir("openrouter_config")
    model_config_path = runtime_dir / "openrouter.model.json"
    key_path = runtime_dir / "openrouter.key"

    model_config_path.write_text(
        json.dumps(
            {
                "base_url": "https://openrouter.ai/api/v1/chat/completions",
                "model": "openrouter/auto",
                "temperature": 0.1,
                "max_tokens": 4000,
                "http_referer": "http://127.0.0.1:3000",
                "x_title": "WorldCup Predictor"
            }
        ),
        encoding="utf-8",
    )
    key_path.write_text("sk-or-v1-test-key\n", encoding="utf-8")

    settings = load_openrouter_settings(str(model_config_path), str(key_path))

    assert settings.base_url == "https://openrouter.ai/api/v1/chat/completions"
    assert settings.model == "openrouter/auto"
    assert settings.api_key == "sk-or-v1-test-key"
    assert settings.temperature == 0.1
    assert settings.max_tokens == 4000
