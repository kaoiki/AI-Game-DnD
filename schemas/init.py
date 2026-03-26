from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from events.types import EventType
from schemas.invoke import EventInfo, InvokeRequest


class InitSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=1, description="本局游戏唯一标识")
    player_count: int = Field(..., ge=1, description="玩家数量")
    difficulty: Literal["EASY", "NORMAL", "HARD"] = Field(..., description="游戏难度")


class InitTime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hard_limit_seconds: int = Field(..., ge=1, description="本局总时长上限")
    elapsed_active_seconds: int = Field(..., ge=0, description="已消耗活跃时间")
    remaining_seconds: int = Field(..., ge=0, description="剩余时间")


class InitSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_seed: str = Field(..., min_length=1, description="本局运行随机种子")


class InitConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str = Field(..., min_length=1, description="输出语言")
    content_rating: str | None = Field(default=None, description="内容分级")
    max_chars_scene: int = Field(..., ge=1, description="场景描述最大字数")
    max_chars_option: int = Field(..., ge=1, description="选项文本最大字数")
    forbidden_terms: list[str] = Field(default_factory=list, description="禁用词列表")


class InitSlots(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone_bias: str | None = Field(default=None, description="风格倾向")
    theme_bias: str | None = Field(default=None, description="主题倾向")
    npc_bias: str | None = Field(default=None, description="NPC 倾向")


class InitClientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Literal["web", "miniprogram", "app"] | None = Field(
        default=None,
        description="客户端平台",
    )
    locale: str | None = Field(default=None, description="地区/语言环境")


class InitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_id: int | None = Field(
        default=None,
        ge=1,
        description="用户选中的上一轮选项 ID。INIT 阶段通常为空。",
    )


class InitContext(BaseModel):
    """
    给未来 db9.ai / 记忆增强 / 外部上下文预留。
    当前阶段不做强约束，只做结构占位。
    """

    model_config = ConfigDict(extra="allow")

    memory_context: dict[str, Any] | None = Field(
        default=None,
        description="外部记忆或增强上下文预留",
    )


class InitRequest(BaseModel):
    """
    INIT 专用输入 schema。
    """

    model_config = ConfigDict(extra="allow")

    event: EventInfo
    session: InitSession
    time: InitTime
    seed: InitSeed
    constraints: InitConstraints
    slots: InitSlots = Field(default_factory=InitSlots)
    client_context: InitClientContext = Field(default_factory=InitClientContext)
    payload: InitPayload = Field(default_factory=InitPayload)
    context: InitContext = Field(default_factory=InitContext)

    @classmethod
    def from_invoke(cls, request: InvokeRequest) -> "InitRequest":
        if request.event.type != EventType.INIT:
            raise ValueError(f"InitRequest only supports event type '{EventType.INIT.value}'")
        return cls.model_validate(request.model_dump())


class OptionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, description="选项 ID")
    text: str = Field(..., min_length=1, description="选项文本")


class InitAiState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_seed: str = Field(..., min_length=1, description="世界观锚点")
    title: str = Field(..., min_length=1, description="当前标题")
    tone: str = Field(..., min_length=1, description="当前氛围")
    memory_summary: str = Field(..., min_length=1, description="剧情摘要")
    arc_progress: int = Field(..., description="剧情进度，INIT 固定为 0")

    @field_validator("arc_progress")
    @classmethod
    def validate_arc_progress(cls, v: int) -> int:
        if v != 0:
            raise ValueError("INIT arc_progress must be 0")
        return v


class InitMainline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    premise: str = Field(..., min_length=1, description="故事前提")
    player_role: str = Field(..., min_length=1, description="玩家身份")
    primary_goal: str = Field(..., min_length=1, description="主要目标")
    stakes: str = Field(..., min_length=1, description="代价或风险")


class InitOpening(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene: str = Field(..., min_length=1, description="开场场景")
    npc_line: str = Field(..., min_length=1, description="NPC 引导台词")


class InitStartHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    how_to_play_next: str = Field(..., min_length=1, description="下一步操作提示")


class InitOutputPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mainline: InitMainline
    opening: InitOpening
    start_hint: InitStartHint
    options: list[OptionItem] = Field(..., description="可执行动作列表")

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

class InitOutputContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_scene_summary: str = Field(..., min_length=1, description="当前场景摘要")
    available_options: list[OptionItem] = Field(..., description="当前可选项快照")
    state_flags: dict[str, Any] = Field(default_factory=dict, description="状态标记")


class InitRouting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_event_type: str = Field(
        ...,
        min_length=1,
        description="下一事件类型建议（由配置控制，使用小写）",
    )
    should_end: bool = Field(..., description="是否应结束流程")

    @field_validator("next_event_type")
    @classmethod
    def validate_next_event_type(cls, v: str) -> str:
        value = v.strip().lower()
        if not value:
            raise ValueError("next_event_type must not be empty")
        return value

    @model_validator(mode="after")
    def validate_should_end(self):
        if self.should_end:
            raise ValueError("INIT should_end must be false")
        return self


class InitMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(..., min_length=1, description="链路追踪 ID")


class InitResponse(BaseModel):
    """
    INIT 专用输出 schema。
    """

    model_config = ConfigDict(extra="forbid")

    event: EventInfo
    ai_state: InitAiState
    payload: InitOutputPayload
    context: InitOutputContext
    routing: InitRouting
    meta: InitMeta

    @classmethod
    def mock(cls) -> "InitResponse":
        return cls(
            event=EventInfo(type=EventType.INIT),
            ai_state=InitAiState(
                world_seed="记忆会被钟塔吞掉",
                title="回声钟塔",
                tone="温柔诡秘",
                memory_summary="你来到一座会吞噬记忆的钟塔。",
                arc_progress=0,
            ),
            payload=InitOutputPayload(
                mainline=InitMainline(
                    premise="钟塔正在吞噬你的关键记忆。",
                    player_role="你是一名被钟塔选中的来访者。",
                    primary_goal="在时间耗尽前找回被吞掉的记忆。",
                    stakes="如果失败，你会忘记自己最重要的人。",
                ),
                opening=InitOpening(
                    scene="你站在钟塔门口，怀表在掌心发烫。",
                    npc_line="想进去，先付出一点代价。",
                ),
                start_hint=InitStartHint(
                    how_to_play_next="请选择一个行动。",
                ),
                options=[
                    OptionItem(id=1, text="交出记忆"),
                    OptionItem(id=2, text="试探对方"),
                ],
            ),
            context=InitOutputContext(
                current_scene_summary="你站在钟塔门口，怀表在掌心发烫，一名神秘守塔人正在注视你。",
                available_options=[
                    OptionItem(id=1, text="交出记忆"),
                    OptionItem(id=2, text="试探对方"),
                ],
                state_flags={},
            ),
            routing=InitRouting(
                next_event_type="DECISION",
                should_end=False,
            ),
            meta=InitMeta(
                trace_id="trace_init_mock_001",
            ),
        )