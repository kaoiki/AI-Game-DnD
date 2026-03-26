from pydantic import BaseModel, ConfigDict, Field


class NovelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_overview: str = Field(..., min_length=1)
    player_journey: str = Field(..., min_length=1)
    final_outcome: str = Field(..., min_length=1)


class NovelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_name: str = Field(..., min_length=1)
    novel_summary: NovelSummary


class NovelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)