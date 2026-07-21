from typing import List
from pydantic import BaseModel, Field, ConfigDict


class AIIntelligenceOutput(BaseModel):
    summary: str = Field(description="Comprehensive executive summary of the meeting")
    tasks: List[str] = Field(default_factory=list, description="Extracted actionable tasks/action items with assignees if mentioned")
    updates: List[str] = Field(default_factory=list, description="Key bullet-point project updates discussed during the meeting")


class AIResultResponse(BaseModel):
    id: str
    meeting_id: str
    summary: str
    tasks: List[str]
    updates: List[str]
    word_count: int
    raw_aggregated_transcript: str
    
    model_config = ConfigDict(from_attributes=True)
