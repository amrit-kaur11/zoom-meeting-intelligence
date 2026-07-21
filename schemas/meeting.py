from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from models.meeting import MeetingStatus
from schemas.ai import AIResultResponse


class TranscriptFileResponse(BaseModel):
    id: str
    file_url: str
    status: str
    file_order: int

    model_config = ConfigDict(from_attributes=True)


class MeetingResponse(BaseModel):
    id: str
    zoom_meeting_id: str
    topic: Optional[str] = None
    status: MeetingStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active_participants: int
    total_participants_joined: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ai_result: Optional[AIResultResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessMeetingRequest(BaseModel):
    zoom_meeting_id: str
    vtt_urls: List[str]
    topic: Optional[str] = "Manual Meeting Trigger"
