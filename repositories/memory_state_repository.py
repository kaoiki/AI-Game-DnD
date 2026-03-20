from threading import Lock
from typing import Any

from repositories.state_repository import StateRepository


class MemoryStateRepository(StateRepository):
    """
    内存版最小状态仓储。

    适合当前 MVP / 本地开发阶段。
    后续如果切 DuckDB，只要保留相同接口即可。
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def save_snapshot(
        self,
        *,
        session_id: str,
        event_type: str,
        ai_state: dict[str, Any],
        last_output: dict[str, Any],
    ) -> None:
        snapshot = {
            "session_id": session_id,
            "event_type": event_type,
            "ai_state": ai_state,
            "last_output": last_output,
        }

        with self._lock:
            self._store[session_id] = snapshot

    def get_snapshot(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._store.get(session_id)