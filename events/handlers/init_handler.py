from events.base import BaseEventHandler
from schemas.invoke import EventInfo, InvokeRequest, InvokeResponseData


class InitEventHandler(BaseEventHandler):
    """
    INIT 事件占位处理器。

    当前阶段：
    - 仅用于打通事件链路
    - 不实现真实 INIT 业务逻辑
    - 返回 mock 数据供 dispatcher / route 验证
    """

    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        return InvokeResponseData(
            event=EventInfo(type=request.event_type),
            payload={
                "message": "mock init handled"
            }
        )