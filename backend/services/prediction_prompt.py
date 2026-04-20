"""核心功能：将预测上下文转换为适合 OpenRouter 调用的 prompt 与请求对象。"""

import json
from typing import Any

from backend.llm.provider import PredictionRequest
from backend.services.prediction_context import PredictionContext
from backend.services.prediction_schema import prediction_output_response_format


def build_prediction_system_prompt() -> str:
    """构建预测智能体系统提示词。"""

    return (
        "You predict football matches using only the supplied JSON facts.\n"
        "Do not browse or retrieve external information.\n"
        "Do not reference, compare, or infer any historical prediction versions.\n"
        "Write all natural-language fields in Simplified Chinese, including reasoning_summary, "
        "evidence_items claims, and uncertainties.\n"
        "Return exactly one compact JSON object with these fields: predicted_score, outcome_pick, "
        "home_goals_pick, away_goals_pick, total_goals_pick, confidence, reasoning_summary, "
        "evidence_items, uncertainties, model_meta, input_snapshot.\n"
        "evidence_items must contain 3 items grounded in the supplied facts.\n"
        "Do not output markdown or chain-of-thought."
    )


def build_prediction_user_prompt(context: PredictionContext) -> str:
    """构建预测智能体用户提示词。"""

    payload = {
        "match_facts": context.match_facts,
        "instructions": [
            "Predict outcome, score, home goals, away goals, total goals and confidence.",
            "Use only the supplied match facts and do not mention any previous prediction versions.",
            "Write reasoning_summary, evidence_items, and uncertainties in Simplified Chinese.",
            "Mark uncertainties clearly when evidence is incomplete.",
            "Use the latest evidence available at prediction time.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_prediction_messages(context: PredictionContext) -> list[dict[str, Any]]:
    """构建 OpenRouter 所需的 messages。"""

    return [
        {"role": "system", "content": build_prediction_system_prompt()},
        {"role": "user", "content": build_prediction_user_prompt(context)},
    ]


def build_prediction_request(
    context: PredictionContext,
    *,
    enable_web_plugin: bool = True,
    enable_response_healing: bool = True,
    require_parameters: bool = True,
    use_response_format: bool = True,
) -> PredictionRequest:
    """构建可直接提交给 provider 的预测请求。"""

    plugins: list[dict[str, Any]] = []
    if enable_web_plugin:
        plugins.append({"id": "web"})
    if enable_response_healing:
        plugins.append({"id": "response-healing"})

    match_id = context.match_facts.get("match_id")

    return PredictionRequest(
        messages=build_prediction_messages(context),
        response_format=prediction_output_response_format() if use_response_format else None,
        plugins=plugins,
        provider={"require_parameters": require_parameters},
        metadata={
            "match_id": match_id,
            "match_facts": context.match_facts,
        },
    )
