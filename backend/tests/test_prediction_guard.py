"""核心功能：验证预测并发保护器对同一场比赛的互斥行为。"""

from backend.services.prediction_guard import InMemoryPredictionGuard


def test_in_memory_prediction_guard_blocks_duplicate_match_acquire_until_release():
    guard = InMemoryPredictionGuard()

    assert guard.acquire("fwc2026-m001") is True
    assert guard.acquire("fwc2026-m001") is False

    guard.release("fwc2026-m001")

    assert guard.acquire("fwc2026-m001") is True
    guard.release("fwc2026-m001")
