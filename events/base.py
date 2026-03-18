from abc import ABC, abstractmethod

from schemas.invoke import InvokeRequest, InvokeResponseData


class BaseEventHandler(ABC):
    """
    所有事件处理器的统一接口约定。
    """

    @abstractmethod
    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        """
        接收统一事件请求，返回统一事件 data 结构。
        """
        raise NotImplementedError