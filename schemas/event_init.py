from pydantic import BaseModel, ConfigDict, Field


class DndEventInitSlots(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone_bias: str = Field(..., min_length=1, description="风格倾向")
    theme_bias: str = Field(..., min_length=1, description="主题倾向")
    npc_bias: str = Field(..., min_length=1, description="NPC 类型")


class DndEventInitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., min_length=1, description="初始化选中的目标事件")
    slots: DndEventInitSlots