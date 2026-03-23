from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from events.types import EventType


class EventInfo(BaseModel):
    type: EventType = Field(..., description="事件类型")


class InvokeRequest(BaseModel):
    """
    通用事件请求入口。

    当前阶段只强约束 event.type，
    其余字段先允许透传，留给第三阶段具体事件再细化。
    """

    model_config = ConfigDict(extra="allow")

    event: EventInfo

    @property
    def event_type(self) -> EventType:
        return self.event.type

    def extra_data(self) -> dict[str, Any]:
        """
        返回除 event 外的其余透传字段，
        方便后续 dispatcher / handler 使用。
        """
        data = self.model_dump()
        data.pop("event", None)
        return data


class InvokeResponseData(BaseModel):
    """
    /invoke 接口的 data 区统一结构。

    注意：
    - 最外层仍由 core.response 统一包装
    - 当前阶段只统一事件响应壳
    - 具体事件内容先放在 payload 中
    """

    event: EventInfo = Field(..., description="当前响应对应的事件信息")
    ai_state: dict[str, Any] = Field(default_factory=dict, description="AI状态数据")
    payload: dict[str, Any] = Field(default_factory=dict, description="事件返回载荷")
    routing: dict[str, Any] = Field(default_factory=dict, description="路由控制信息")
    context: dict[str, Any] = Field(default_factory=dict, description="事件上下文")
    meta: dict[str, Any] = Field(default_factory=dict, description="元信息")
    