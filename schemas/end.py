from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from events.types import EventType
from schemas.invoke import EventInfo, InvokeRequest
from schemas.init import (
    InitClientContext,
    InitConstraints,
    InitSeed,
    InitSession,
    InitSlots,
    InitTime,
)


class EndAiState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_seed: str = Field(..., min_length=1, description="世界观锚点")
    title: str = Field(..., min_length=1, description="当前标题")
    tone: str = Field(..., min_length=1, description="当前氛围")
    memory_summary: str = Field(..., min_length=1, description="剧情摘要")
    arc_progress: int = Field(..., ge=0, description="剧情进度，END 阶段允许非 0")


class EndPayloadIn(BaseModel):
    """
    END 阶段没有强制输入动作，保留空壳即可，
    继续兼容统一协议中的 payload 字段。
    """
    model_config = ConfigDict(extra="forbid")


class HistoryEventItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=1, description="历史事件类型，小写")
    scene_summary: str = Field(default="", description="该事件阶段的场景摘要")
    selected_option_text: str = Field(default="", description="该事件中的玩家选择文本")
    result_summary: str = Field(default="", description="该事件带来的结果摘要")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        value = v.strip().lower()
        if not value:
            raise ValueError("history event_type must not be empty")
        return value


class EndContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_scene_summary: str = Field(..., min_length=1, description="当前终局场景摘要")
    available_options: list[Any] = Field(
        default_factory=list,
        description="END 为终局事件，固定为空数组"
    )
    state_flags: dict[str, Any] = Field(default_factory=dict, description="状态标记")
    history_events: list[HistoryEventItem] | None = Field(
        default=None,
        description="整局历史事件摘要（可选）"
    )

    @model_validator(mode="after")
    def validate_available_options_empty(self):
        if self.available_options != []:
            raise ValueError("END context.available_options must be an empty list")
        return self


class EndRequest(BaseModel):
    """
    END 专用输入 schema。
    继续沿用统一壳，差异只体现在 payload / context。
    """

    model_config = ConfigDict(extra="allow")

    event: EventInfo
    session: InitSession
    time: InitTime
    seed: InitSeed
    constraints: InitConstraints
    slots: InitSlots = Field(default_factory=InitSlots)
    client_context: InitClientContext = Field(default_factory=InitClientContext)
    payload: EndPayloadIn = Field(default_factory=EndPayloadIn)
    context: EndContext

    @classmethod
    def from_invoke(cls, request: InvokeRequest) -> "EndRequest":
        if request.event.type != EventType.END:
            raise ValueError(
                f"EndRequest only supports event type '{EventType.END.value}'"
            )
        return cls.model_validate(request.model_dump())


class Ending(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="结局标题")
    outcome: str = Field(..., min_length=1, description="最终结果")


class Epilogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene: str = Field(..., min_length=1, description="结尾场景")
    closing_line: str = Field(..., min_length=1, description="结尾句")


class KeyChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=1, description="关键选择对应的事件类型")
    choice_text: str = Field(..., min_length=1, description="玩家选择内容")
    impact: str = Field(..., min_length=1, description="该选择对结局的影响")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        value = v.strip().lower()
        if not value:
            raise ValueError("key choice event_type must not be empty")
        return value


class NovelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_overview: str = Field(..., min_length=1, description="故事整体概述")
    player_journey: str = Field(..., min_length=1, description="玩家旅程摘要")
    final_outcome: str = Field(..., min_length=1, description="最终结局摘要")


class EndPayloadOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ending: Ending
    epilogue: Epilogue
    key_choices: list[KeyChoice] = Field(..., description="关键选择列表")
    novel_summary: NovelSummary

    @field_validator("key_choices")
    @classmethod
    def validate_key_choices_length(cls, v: list[KeyChoice]) -> list[KeyChoice]:
        if not 1 <= len(v) <= 5:
            raise ValueError("key_choices length must be between 1 and 5")
        return v


class EndRouting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_event_type: EventType = Field(..., description="下一事件类型，END 固定为 end")
    should_end: bool = Field(..., description="是否结束，END 固定为 true")

    @field_validator("next_event_type")
    @classmethod
    def validate_next_event_type(cls, v: EventType) -> EventType:
        if v != EventType.END:
            raise ValueError("end routing.next_event_type must be end")
        return v

    @model_validator(mode="after")
    def validate_should_end_consistency(self):
        if self.should_end is not True:
            raise ValueError("when next_event_type is end, should_end must be true")
        return self


class EndMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1, description="链路追踪 ID")


class EndResponse(BaseModel):
    """
    END 专用输出 schema。
    外层保持统一，差异集中在 payload / context / routing。
    """

    model_config = ConfigDict(extra="forbid")

    event: EventInfo
    ai_state: EndAiState
    payload: EndPayloadOut
    context: EndContext
    routing: EndRouting
    meta: EndMeta

    @model_validator(mode="after")
    def validate_event_type_and_context_alignment(self):
        if self.event.type != EventType.END:
            raise ValueError("EndResponse event.type must be end")

        if self.context.available_options != []:
            raise ValueError("END context.available_options must be []")

        return self