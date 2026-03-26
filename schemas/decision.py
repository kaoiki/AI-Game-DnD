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

class DecisionAiState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_seed: str = Field(..., min_length=1, description="世界观锚点")
    title: str = Field(..., min_length=1, description="当前标题")
    tone: str = Field(..., min_length=1, description="当前氛围")
    memory_summary: str = Field(..., min_length=1, description="剧情摘要")
    arc_progress: int = Field(..., ge=0, description="剧情进度，DECISION 阶段允许非 0")

class DecisionPayloadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")


class DecisionContext(BaseModel):
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


class DecisionRequest(BaseModel):
    """
    DECISION 专用输入 schema。
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
    payload: DecisionPayloadIn
    context: DecisionContext

    @classmethod
    def from_invoke(cls, request: InvokeRequest) -> "DecisionRequest":
        if request.event.type != EventType.DECISION:
            raise ValueError(
                f"DecisionRequest only supports event type '{EventType.DECISION.value}'"
            )
        return cls.model_validate(request.model_dump())

    @model_validator(mode="after")
    def validate_selected_option_exists(self):
        option_ids = {item.id for item in self.context.available_options}
        if self.payload.selected_option_id not in option_ids:
            raise ValueError("selected_option_id must exist in context.available_options")
        return self


class SelectedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")
    selected_option_text: str = Field(..., min_length=1, description="本次选择对应的选项文本")

    @field_validator("selected_option_text")
    @classmethod
    def validate_selected_option_text(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("selected_option_text must not be empty")
        return value

    model_config = ConfigDict(extra="forbid")

    selected_option_id: int = Field(..., ge=1, description="玩家本次选择的选项 ID")
    selected_option_text: str = Field(..., min_length=1, description="本次选择对应的选项文本")


class DecisionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(..., min_length=1, description="本次选择带来的直接剧情结果")
    effect: str = Field(..., min_length=1, description="本次结果对局面/角色/线索造成的影响")


class DecisionScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=1, description="推进后的当前场景描述")
    npc_line: str = Field(..., min_length=1, description="NPC 当前回应或提示")


class DecisionPayloadOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: SelectedAction
    result: DecisionOutcome
    scene: DecisionScene
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


class DecisionRouting(BaseModel):
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
                "decision routing.next_event_type must be one of: "
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


class DecisionMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1, description="链路追踪 ID")


class DecisionResponse(BaseModel):
    """
    DECISION 专用输出 schema。
    外层保持统一，差异集中在 payload / context / routing。
    """

    model_config = ConfigDict(extra="forbid")

    event: EventInfo
    ai_state: DecisionAiState
    payload: DecisionPayloadOut
    context: DecisionContext
    routing: DecisionRouting
    meta: DecisionMeta

    @model_validator(mode="after")
    def validate_event_type_and_context_alignment(self):
        if self.event.type != EventType.DECISION:
            raise ValueError("DecisionResponse event.type must be decision")

        payload_options = [(item.id, item.text) for item in self.payload.options]
        context_options = [(item.id, item.text) for item in self.context.available_options]
        if payload_options != context_options:
            raise ValueError("context.available_options must align with payload.options")

        # 这里只校验“输出中记录的选择文本”本身合法非空；
        # 不强制要求它必须等于上一轮 options 的 text，
        # 因为 handler 里会更稳地从输入 context 反查并覆盖。
        return self

    @classmethod
    def mock(cls) -> "DecisionResponse":
        return cls(
            event=EventInfo(type=EventType.DECISION),
            ai_state=DecisionAiState(
                world_seed="run_test_001_蒸汽都市连环谜案",
                title="齿轮下的低语",
                tone="悬疑诡谲",
                memory_summary="玩家追问仿生人的记忆碎片，逐步逼近钟楼谜案的核心。",
                arc_progress=20,
            ),
            payload=DecisionPayloadOut(
                decision=SelectedAction(
                    selected_option_id=2,
                    selected_option_text="追问记忆细节",
                ),
                result=DecisionOutcome(
                    outcome="仿生人在混乱记忆中提到一枚刻有钟楼纹章的铜片。",
                    effect="你获得新的关键线索，但仿生人的状态更加不稳定。",
                ),
                scene=DecisionScene(
                    summary="浓雾更重了，远处的蒸汽阀门发出尖啸，工坊区像在召唤你前去。",
                    npc_line="“那里……有钟声，也有火。”",
                ),
                options=[
                    OptionItem(id=1, text="前往钟楼工坊"),
                    OptionItem(id=2, text="安抚仿生人"),
                    OptionItem(id=3, text="继续追问铜片"),
                ],
            ),
            context=DecisionContext(
                current_scene_summary="侦探获得钟楼线索，准备决定下一步行动。",
                available_options=[
                    OptionItem(id=1, text="前往钟楼工坊"),
                    OptionItem(id=2, text="安抚仿生人"),
                    OptionItem(id=3, text="继续追问铜片"),
                ],
                state_flags={"found_clocktower_clue": True},
            ),
            routing=DecisionRouting(
                next_event_type=EventType.DECISION,
                should_end=False,
            ),
            meta=DecisionMeta(
                trace_id="decision_run_test_001_002",
            ),
        )