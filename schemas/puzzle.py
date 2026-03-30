from typing import Any, Literal, Optional

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


class PuzzleAiState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_seed: str = Field(..., min_length=1, description="世界观锚点")
    title: str = Field(..., min_length=1, description="当前标题")
    tone: str = Field(..., min_length=1, description="当前氛围")
    memory_summary: str = Field(..., min_length=1, description="剧情摘要")
    arc_progress: int = Field(..., ge=0, description="剧情进度，PUZZLE 阶段允许非 0")


class PuzzlePayloadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")


class PuzzleContext(BaseModel):
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


class PuzzleRequest(BaseModel):
    """
    PUZZLE 专用输入 schema。
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
    payload: PuzzlePayloadIn
    context: PuzzleContext

    @classmethod
    def from_invoke(cls, request: InvokeRequest) -> "PuzzleRequest":
        if request.event.type != EventType.PUZZLE:
            raise ValueError(
                f"PuzzleRequest only supports event type '{EventType.PUZZLE.value}'"
            )
        return cls.model_validate(request.model_dump())

    @model_validator(mode="after")
    def validate_selected_option_exists(self):
        option_ids = {item.id for item in self.context.available_options}
        if self.payload.selected_option_id not in option_ids:
            raise ValueError("selected_option_id must exist in context.available_options")
        return self


class PuzzleCore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="谜题标题")
    riddle: str = Field(..., min_length=1, description="谜题谜面或机关描述")
    hint_level: int = Field(..., ge=0, le=3, description="提示层级，0 表示不额外提示")
    key_fact: str = Field(..., min_length=1, description="谜题判定依据的关键事实")

    @field_validator("title", "riddle", "key_fact")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("puzzle text field must not be empty")
        return value


class PuzzleAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")
    selected_option_text: str = Field(..., min_length=1, description="本次选择对应的选项文本")
    is_correct: bool = Field(..., description="本次尝试是否正确")

    @field_validator("selected_option_text")
    @classmethod
    def validate_selected_option_text(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("selected_option_text must not be empty")
        return value


class PuzzleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(..., min_length=1, description="本次尝试的直接结果")
    consequence: str = Field(..., min_length=1, description="该结果带来的后果描述")
    failure_level: Literal["none", "minor", "major", "deadly"] = Field(
        ...,
        description="失败等级：none/minor/major/deadly",
    )
    enemy_triggered: bool = Field(..., description="是否因本次结果引来了敌人")

    @field_validator("outcome", "consequence")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("result text field must not be empty")
        return value

    @model_validator(mode="after")
    def validate_result_consistency(self):
        if self.failure_level == "deadly" and self.enemy_triggered:
            raise ValueError("deadly result should not also set enemy_triggered=true")
        return self


class PuzzleScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=1, description="判定后的当前场景描述")
    npc_line: str = Field(..., min_length=1, description="NPC 当前回应或提示")

    @field_validator("summary", "npc_line")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("scene text field must not be empty")
        return value


class PuzzlePayloadOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    puzzle: Optional[PuzzleCore] = None
    attempt: PuzzleAttempt
    result: PuzzleResult
    scene: PuzzleScene
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


class PuzzleRouting(BaseModel):
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
                "puzzle routing.next_event_type must be one of: "
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


class PuzzleMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1, description="链路追踪 ID")


class PuzzleResponse(BaseModel):
    """
    PUZZLE 专用输出 schema。
    外层保持统一，差异集中在 payload / context / routing。
    """

    model_config = ConfigDict(extra="forbid")

    event: EventInfo
    ai_state: PuzzleAiState
    payload: PuzzlePayloadOut
    context: PuzzleContext
    routing: PuzzleRouting
    meta: PuzzleMeta

    @model_validator(mode="after")
    def validate_event_type_and_context_alignment(self):
        if self.event.type != EventType.PUZZLE:
            raise ValueError("PuzzleResponse event.type must be puzzle")

        payload_options = [(item.id, item.text) for item in self.payload.options]
        context_options = [(item.id, item.text) for item in self.context.available_options]
        if payload_options != context_options:
            raise ValueError("context.available_options must align with payload.options")

        return self

    @model_validator(mode="after")
    def validate_forced_route_semantics(self):
        result = self.payload.result
        routing = self.routing

        if result.failure_level == "deadly":
            if routing.next_event_type != EventType.END:
                raise ValueError("deadly puzzle result must route to end")
            if not routing.should_end:
                raise ValueError("deadly puzzle result must set should_end=true")

        if result.enemy_triggered:
            if routing.next_event_type != EventType.COMBAT:
                raise ValueError("enemy-triggered puzzle result must route to combat")
            if routing.should_end:
                raise ValueError("combat route must set should_end=false")

        return self

