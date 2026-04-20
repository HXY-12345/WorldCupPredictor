"""核心功能：校验、规范化和导出预测智能体的结构化输出 schema。"""

from datetime import datetime
from enum import StrEnum
import json
import re
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from backend.llm.provider import PredictionProviderError

PREDICTION_SCHEMA_NAME = "worldcup_prediction_output"
DEFAULT_EVIDENCE_SOURCE_URL = "https://worldcup.invalid/prediction-input"


class PredictionSchemaError(PredictionProviderError):
    """预测输出 schema 校验失败。"""


class PredictionOutcomePick(StrEnum):
    """比赛结果倾向。"""

    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"


class PredictionScore(BaseModel):
    """预测比分。"""

    model_config = ConfigDict(extra="forbid")

    home: int = Field(ge=0, le=20)
    away: int = Field(ge=0, le=20)


class PredictionEvidenceItem(BaseModel):
    """预测证据项。"""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_url: AnyHttpUrl
    source_level: int = Field(ge=1, le=4)


class PredictionModelMeta(BaseModel):
    """预测模型元信息。"""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    predicted_at: datetime


class PredictionInputSnapshot(BaseModel):
    """预测输入快照。"""

    model_config = ConfigDict(extra="forbid")

    match_id: str = Field(min_length=1)
    official_match_number: int | None = None
    kickoff_label: str | None = None
    sort_order: int | None = None
    date: str = Field(min_length=1)
    time: str | None = None
    stage: str | None = None
    group_name: str | None = None
    venue: str | None = None
    home_team: dict[str, Any]
    away_team: dict[str, Any]
    status: str | None = None
    score: dict[str, Any] | None = None
    prediction: dict[str, Any] | None = None


class PredictionOutput(BaseModel):
    """结构化预测输出。"""

    model_config = ConfigDict(extra="forbid")

    predicted_score: PredictionScore
    outcome_pick: PredictionOutcomePick
    home_goals_pick: int = Field(ge=0, le=20)
    away_goals_pick: int = Field(ge=0, le=20)
    total_goals_pick: int = Field(ge=0, le=40)
    confidence: int = Field(ge=0, le=100)
    reasoning_summary: str = Field(min_length=1)
    evidence_items: list[PredictionEvidenceItem]
    uncertainties: list[str] = Field(default_factory=list)
    model_meta: PredictionModelMeta
    input_snapshot: PredictionInputSnapshot

    @field_validator("confidence", mode="before")
    @classmethod
    def _normalize_confidence(cls, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
        if isinstance(value, str):
            stripped = value.strip().replace("%", "")
            if stripped:
                confidence_labels = {
                    "低": 35,
                    "较低": 40,
                    "中": 55,
                    "中等": 55,
                    "较高": 70,
                    "高": 80,
                }
                if stripped in confidence_labels:
                    return confidence_labels[stripped]
                try:
                    return int(round(float(stripped)))
                except ValueError:
                    match = re.search(r"(\d+(?:\.\d+)?)", stripped)
                    if match:
                        return int(round(float(match.group(1))))
        return value

    @field_validator("evidence_items")
    @classmethod
    def _validate_evidence_items(cls, value: list[PredictionEvidenceItem]) -> list[PredictionEvidenceItem]:
        if not 3 <= len(value) <= 5:
            raise ValueError("Prediction must include 3 to 5 evidence items.")
        return value

    @model_validator(mode="after")
    def _validate_consistency(self) -> "PredictionOutput":
        if self.predicted_score.home != self.home_goals_pick or self.predicted_score.away != self.away_goals_pick:
            raise ValueError("predicted_score must match home_goals_pick and away_goals_pick.")

        if self.total_goals_pick != self.home_goals_pick + self.away_goals_pick:
            raise ValueError("total_goals_pick must equal home_goals_pick + away_goals_pick.")

        expected_outcome = _derive_outcome(self.predicted_score.home, self.predicted_score.away)
        if self.outcome_pick != expected_outcome:
            raise ValueError("outcome_pick must match the predicted score.")

        return self


def parse_prediction_output(raw_output: Any) -> PredictionOutput:
    """解析并校验预测输出。"""

    try:
        payload = coerce_prediction_payload(raw_output)
        return PredictionOutput.model_validate(payload)
    except ValidationError as error:
        raise PredictionSchemaError(str(error)) from error
    except ValueError as error:
        raise PredictionSchemaError(str(error)) from error


def prediction_output_json_schema() -> dict[str, Any]:
    """导出预测输出的 JSON Schema。"""

    return PredictionOutput.model_json_schema()


def prediction_output_response_format() -> dict[str, Any]:
    """导出 OpenRouter 需要的 response_format。"""

    return {
        "type": "json_schema",
        "json_schema": {
            "name": PREDICTION_SCHEMA_NAME,
            "strict": True,
            "schema": prediction_output_json_schema(),
        },
    }


def coerce_prediction_payload(raw_output: Any) -> Any:
    """把模型原始输出转成尽量接近目标 schema 的 Python 对象。"""

    if isinstance(raw_output, PredictionOutput):
        return raw_output.model_dump()
    if isinstance(raw_output, (bytes, bytearray)):
        raw_output = raw_output.decode("utf-8")
    if isinstance(raw_output, str):
        raw_output = json.loads(_extract_json_object_text(raw_output))
    return _normalize_payload(raw_output)


def _extract_json_object_text(raw_output: str) -> str:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Prediction output was empty.")

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        return stripped[first_brace : last_brace + 1]
    return stripped


def _normalize_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    predicted_score = _normalize_predicted_score(
        normalized.get("predicted_score"),
        normalized.get("home_goals_pick"),
        normalized.get("away_goals_pick"),
    )
    if predicted_score is not None:
        normalized["predicted_score"] = predicted_score
        normalized["home_goals_pick"] = _to_int(normalized.get("home_goals_pick"), predicted_score["home"])
        normalized["away_goals_pick"] = _to_int(normalized.get("away_goals_pick"), predicted_score["away"])
        normalized["total_goals_pick"] = _to_int(
            normalized.get("total_goals_pick"),
            normalized["home_goals_pick"] + normalized["away_goals_pick"],
        )
        normalized["outcome_pick"] = _normalize_outcome(
            normalized.get("outcome_pick"),
            normalized["home_goals_pick"],
            normalized["away_goals_pick"],
        )

    normalized["evidence_items"] = _normalize_evidence_items(normalized.get("evidence_items"))
    normalized["uncertainties"] = _normalize_uncertainties(normalized.get("uncertainties"))
    normalized["model_meta"] = _normalize_model_meta(normalized.get("model_meta"))
    normalized["input_snapshot"] = _normalize_input_snapshot(normalized.get("input_snapshot"))
    return normalized


def _normalize_predicted_score(
    value: Any,
    home_goals_pick: Any,
    away_goals_pick: Any,
) -> dict[str, int] | None:
    if isinstance(value, dict):
        home = _to_int(value.get("home"))
        away = _to_int(value.get("away"))
        if home is not None and away is not None:
            return {"home": home, "away": away}

    if isinstance(value, (list, tuple)) and len(value) == 2:
        home = _to_int(value[0])
        away = _to_int(value[1])
        if home is not None and away is not None:
            return {"home": home, "away": away}

    if isinstance(value, str):
        score_match = re.search(r"(\d+)\s*[-:]\s*(\d+)", value)
        if score_match:
            return {"home": int(score_match.group(1)), "away": int(score_match.group(2))}

    home = _to_int(home_goals_pick)
    away = _to_int(away_goals_pick)
    if home is not None and away is not None:
        return {"home": home, "away": away}
    return None


def _normalize_outcome(value: Any, home_goals: int, away_goals: int) -> Any:
    if isinstance(value, str):
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "home": "home_win",
            "home_win": "home_win",
            "homewins": "home_win",
            "away": "away_win",
            "away_win": "away_win",
            "awaywins": "away_win",
            "draw": "draw",
            "tie": "draw",
        }
        if normalized in mapping:
            return mapping[normalized]

    if isinstance(home_goals, int) and isinstance(away_goals, int):
        return _derive_outcome(home_goals, away_goals).value
    return value


def _normalize_evidence_items(value: Any) -> Any:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return value

    normalized_items: list[Any] = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, dict):
            normalized_items.append(item)
            continue
        if isinstance(item, str):
            normalized_items.append(
                {
                    "claim": item,
                    "source_name": "provided_input",
                    "source_url": f"{DEFAULT_EVIDENCE_SOURCE_URL}/{index}",
                    "source_level": 4,
                }
            )
    return normalized_items


def _normalize_uncertainties(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _normalize_model_meta(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    provider = value.get("provider")
    if provider is not None:
        normalized["provider"] = provider

    model_name = value.get("model_name") or value.get("model_version")
    if model_name is not None:
        normalized["model_name"] = model_name

    predicted_at = value.get("predicted_at") or value.get("prediction_time") or value.get("timestamp")
    if predicted_at is not None:
        normalized["predicted_at"] = predicted_at

    return normalized


def _normalize_input_snapshot(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    if isinstance(value.get("match_facts"), dict):
        value = value["match_facts"]

    normalized = dict(value)
    if "group_name" not in normalized and "group" in normalized:
        normalized["group_name"] = normalized["group"]
    if isinstance(normalized.get("home_team"), str):
        normalized["home_team"] = {"name": normalized["home_team"]}
    if isinstance(normalized.get("away_team"), str):
        normalized["away_team"] = {"name": normalized["away_team"]}
    return normalized


def _to_int(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return default


def _derive_outcome(home_goals: int, away_goals: int) -> PredictionOutcomePick:
    if home_goals > away_goals:
        return PredictionOutcomePick.HOME_WIN
    if home_goals < away_goals:
        return PredictionOutcomePick.AWAY_WIN
    return PredictionOutcomePick.DRAW
