from abc import ABC, abstractmethod
from typing import Any


class StateRepository(ABC):
    """
    最小状态仓储接口。

    当前阶段目标：
    - 保存一份会话快照
    - 按 session_id 读取会话快照

    未来可以有：
    - MemoryStateRepository
    - DuckDBStateRepository
    - db9增强写入适配层（不是替代本仓储）
    """

    @abstractmethod
    def save_snapshot(
        self,
        *,
        session_id: str,
        event_type: str,
        ai_state: dict[str, Any],
        last_output: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_snapshot(self, session_id: str) -> dict[str, Any] | None:
        raise NotImplementedError