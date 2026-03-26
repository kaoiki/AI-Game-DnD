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
    OptionItem,
)


class CombatAiState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_seed: str = Field(..., min_length=1, description="世界观锚点")
    title: str = Field(..., min_length=1, description="当前标题")
    tone: str = Field(..., min_length=1, description="当前氛围")
    memory_summary: str = Field(..., min_length=1, description="剧情摘要")
    arc_progress: int = Field(..., ge=0, description="剧情进度，COMBAT 阶段允许非 0")


class CombatPayloadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")


class CombatContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_scene_summary: str = Field(..., min_length=1, description="上一事件传下来的当前场景摘要")
    available_options: list[OptionItem] = Field(..., description="上一事件提供的可选项快照")
    state_flags: dict[str, Any] = Field(default_factory=dict, description="状态标记")

    @field_validator("available_options")
    @classmethod
    def validate_available_options_length(cls, v: list[OptionItem]) -> list[OptionItem]:
        if not 2 <= len(v) <= 4:
            raise ValueError("available_options length must be between 2 and 4")
        return v

    @model_validator(mode="after")
    def validate_available_option_ids_unique(self):
        ids = [item.id for item in self.available_options]
        if len(ids) != len(set(ids)):
            raise ValueError("available option ids must be unique")
        return self


class CombatRequest(BaseModel):
    """
    COMBAT 专用输入 schema。
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
    payload: CombatPayloadIn
    context: CombatContext

    @classmethod
    def from_invoke(cls, request: InvokeRequest) -> "CombatRequest":
        if request.event.type != EventType.COMBAT:
            raise ValueError(
                f"CombatRequest only supports event type '{EventType.COMBAT.value}'"
            )
        return cls.model_validate(request.model_dump())

    @model_validator(mode="after")
    def validate_selected_option_exists(self):
        option_ids = {item.id for item in self.context.available_options}
        if self.payload.selected_option_id not in option_ids:
            raise ValueError("selected_option_id must exist in context.available_options")
        return self

class CombatResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_action: str = Field(..., min_length=1, description="玩家本回合动作")
    enemy_action: str = Field(..., min_length=1, description="敌方本回合动作")
    outcome: str = Field(..., min_length=1, description="本回合结果摘要")
    damage_to_enemy: int = Field(..., ge=0, description="本回合对敌伤害")
    damage_to_player: int = Field(..., ge=0, description="本回合玩家受到伤害")

    @field_validator("player_action", "enemy_action", "outcome")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("text field must not be empty")
        return value


class CombatScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=1, description="推进后的当前战斗场景描述")


class CombatPayloadOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: CombatResult
    scene: CombatScene
    options: list[OptionItem] = Field(..., description="下一步可执行动作列表")

    @field_validator("options")
    @classmethod
    def validate_options_length(cls, v: list[OptionItem]) -> list[OptionItem]:
        if not 2 <= len(v) <= 4:
            raise ValueError("options length must be between 2 and 4")
        return v

    @model_validator(mode="after")
    def validate_option_ids_unique(self):
        ids = [item.id for item in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("option ids must be unique")
        return self


class CombatRouting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_event_type: EventType = Field(..., description="下一事件类型建议")
    should_end: bool = Field(..., description="是否应结束流程")

    @field_validator("next_event_type")
    @classmethod
    def validate_next_event_type(cls, v: EventType) -> EventType:
        allowed = {
            EventType.DECISION,
            EventType.COMBAT,
            EventType.PUZZLE,
            EventType.END,
        }
        if v not in allowed:
            raise ValueError(
                "combat routing.next_event_type must be one of: "
                "decision, combat, puzzle, end"
            )
        return v

    @model_validator(mode="after")
    def validate_should_end_consistency(self):
        if self.should_end and self.next_event_type != EventType.END:
            raise ValueError("when should_end is true, next_event_type must be end")
        if not self.should_end and self.next_event_type == EventType.END:
            raise ValueError("when next_event_type is end, should_end must be true")
        return self


class CombatMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1, description="链路追踪 ID")


class CombatResponse(BaseModel):
    """
    COMBAT 专用输出 schema。
    外层保持统一，差异集中在 payload / context / routing。
    """

    model_config = ConfigDict(extra="forbid")

    event: EventInfo
    ai_state: CombatAiState
    payload: CombatPayloadOut
    context: CombatContext
    routing: CombatRouting
    meta: CombatMeta

    @model_validator(mode="after")
    def validate_event_type_and_context_alignment(self):
        if self.event.type != EventType.COMBAT:
            raise ValueError("CombatResponse event.type must be combat")

        payload_options = [(item.id, item.text) for item in self.payload.options]
        context_options = [(item.id, item.text) for item in self.context.available_options]
        if payload_options != context_options:
            raise ValueError("context.available_options must align with payload.options")

        return self