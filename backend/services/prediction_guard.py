"""核心功能：提供同一场比赛预测请求的进程内互斥保护。"""

from threading import Lock
from typing import Protocol, runtime_checkable


@runtime_checkable
class PredictionExecutionGuard(Protocol):
    """预测执行互斥器协议。"""

    def acquire(self, match_id: str) -> bool:
        """尝试占用指定比赛的预测执行权。"""

    def release(self, match_id: str) -> None:
        """释放指定比赛的预测执行权。"""


class InMemoryPredictionGuard(PredictionExecutionGuard):
    """基于进程内锁的同场比赛预测互斥器。"""

    def __init__(self) -> None:
        self._registry_lock = Lock()
        self._match_locks: dict[str, Lock] = {}

    def acquire(self, match_id: str) -> bool:
        with self._registry_lock:
            lock = self._match_locks.get(match_id)
            if lock is None:
                lock = Lock()
                self._match_locks[match_id] = lock
        return lock.acquire(blocking=False)

    def release(self, match_id: str) -> None:
        with self._registry_lock:
            lock = self._match_locks.get(match_id)
        if lock is not None and lock.locked():
            lock.release()
