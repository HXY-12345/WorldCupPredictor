"""核心功能：验证 decider 阶段会把 evidence bundle 注入预测上下文并落最终版本。"""

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.core.config import Settings
from backend.main import create_app
from backend.models.prediction_version import PredictionVersion
from backend.services.prediction_decider import decide_prediction


def _runtime_dir(prefix: str) -> Path:
    runtime_dir = Path("backend/tests/runtime") / f"{prefix}_{uuid4().hex}"
    runtime_dir.mkdir(parents=True, exist_ok=False)
    return runtime_dir


def _write_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "id": "fwc2026-m001",
                        "official_match_number": 1,
                        "kickoff_label": "M001",
                        "sort_order": 1,
                        "date": "2026-06-11",
                        "time": "18:00",
                        "stage": "Group Stage",
                        "group": "A",
                        "venue": "Mexico City Stadium",
                        "home_team": {
                            "name": "Mexico",
                            "flag": "MX",
                            "fifa_rank": 12,
                            "form": ["W", "D", "W"],
                        },
                        "away_team": {
                            "name": "South Africa",
                            "flag": "ZA",
                            "fifa_rank": 47,
                            "form": ["D", "L", "W"],
                        },
                        "status": "not_started",
                        "score": None,
                        "prediction": None,
                        "head_to_head": None,
                        "key_players": None,
                    }
                ],
                "last_updated": "2026-03-31T00:00:00Z",
                "total": 1,
            }
        ),
        encoding="utf-8",
    )


class RecordingPredictionProvider:
    def __init__(self) -> None:
        self.requests = []

    def predict(self, request):
        self.requests.append(request)
        match_facts = request.metadata["match_facts"]
        return {
            "predicted_score": {"home": 2, "away": 1},
            "outcome_pick": "home_win",
            "home_goals_pick": 2,
            "away_goals_pick": 1,
            "total_goals_pick": 3,
            "confidence": 77,
            "reasoning_summary": "结合证据包判断主队优势更明显。",
            "evidence_items": [
                {
                    "claim": "证据包显示主队状态更稳。",
                    "source_name": "evidence_bundle",
                    "source_url": "https://worldcup.invalid/evidence/1",
                    "source_level": 2,
                },
                {
                    "claim": "主场环境对主队更有利。",
                    "source_name": "evidence_bundle",
                    "source_url": "https://worldcup.invalid/evidence/2",
                    "source_level": 2,
                },
                {
                    "claim": "客队近期波动较大。",
                    "source_name": "evidence_bundle",
                    "source_url": "https://worldcup.invalid/evidence/3",
                    "source_level": 2,
                },
            ],
            "uncertainties": ["临场阵容仍需观察。"],
            "model_meta": {
                "provider": "recording-test",
                "model_name": "recording-model-v1",
                "predicted_at": "2026-04-19T12:00:00Z",
            },
            "input_snapshot": match_facts,
        }


def test_decide_prediction_passes_evidence_bundle_into_prediction_context():
    runtime_dir = _runtime_dir("prediction_decider")
    fixture_path = runtime_dir / "schedule.json"
    _write_fixture(fixture_path)
    database_path = runtime_dir / "prediction_decider.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        enable_fixture_seed=True,
        fixture_seed_path=str(fixture_path),
    )
    app = create_app(settings)
    provider = RecordingPredictionProvider()
    evidence_bundle = {
        "match_id": "fwc2026-m001",
        "home_support": ["Mexico recent form is stronger."],
        "away_support": ["South Africa can still threaten in transition."],
        "neutral_factors": ["Group stage opener can be conservative."],
        "market_view": ["Market leans slightly toward Mexico."],
        "conflicts": [],
        "high_confidence_summary": ["Mexico carries the stronger pre-match profile."],
    }

    with TestClient(app):
        created_prediction = decide_prediction(
            app.state.session_factory,
            "fwc2026-m001",
            evidence_bundle=evidence_bundle,
            provider=provider,
        )

    assert created_prediction.prediction["confidence"] == 77
    user_prompt = provider.requests[0].messages[1]["content"]
    assert '"database_context"' in user_prompt
    assert "Mexico carries the stronger pre-match profile." in user_prompt

    with app.state.session_factory() as session:
        versions = session.scalars(select(PredictionVersion)).all()

    assert len(versions) == 1
