from events.base import BaseEventHandler
from events.types import EventType
from schemas.invoke import InvokeRequest, InvokeResponseData


class EventDispatcher:
    """
    事件分发器。

    职责：
    - 维护 event_type -> handler 的映射
    - 根据请求中的 event.type 找到对应 handler
    - 调用 handler 并返回统一事件响应结构
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, BaseEventHandler] = {}

    def register(self, event_type: EventType, handler: BaseEventHandler) -> None:
        """
        注册事件处理器。
        """
        self._handlers[event_type] = handler

    def get_handler(self, event_type: EventType) -> BaseEventHandler | None:
        """
        根据事件类型获取处理器。
        """
        return self._handlers.get(event_type)

    def dispatch(self, request: InvokeRequest) -> InvokeResponseData:
        """
        分发事件请求到对应 handler。
        """
        handler = self.get_handler(request.event_type)
        if handler is None:
            raise ValueError(f"No handler registered for event type: {request.event_type}")

        return handler.handle(request)