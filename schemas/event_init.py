from pydantic import BaseModel, ConfigDict, Field


class DndEventInitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone_bias: str = Field(..., min_length=1, description="风格倾向")
    theme_bias: str = Field(..., min_length=1, description="主题倾向")
    npc_bias: str = Field(..., min_length=1, description="NPC 类型")