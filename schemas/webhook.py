from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ZoomRecordingFile(BaseModel):
    id: Optional[str] = None
    meeting_id: Optional[str] = None
    file_type: Optional[str] = None  # e.g., "TRANSCRIPT" or "VTT"
    file_extension: Optional[str] = None  # e.g. "VTT"
    download_url: Optional[str] = None
    status: Optional[str] = None


class ZoomObjectPayload(BaseModel):
    id: Optional[str] = None
    uuid: Optional[str] = None
    topic: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    participant: Optional[Dict[str, Any]] = None
    recording_files: Optional[List[ZoomRecordingFile]] = None


class ZoomPayload(BaseModel):
    account_id: Optional[str] = None
    object: ZoomObjectPayload = Field(default_factory=ZoomObjectPayload)


class ZoomWebhookEvent(BaseModel):
    event: str
    event_ts: Optional[int] = None
    payload: ZoomPayload
    event_id: Optional[str] = None  # Can be passed in body or header X-Zm-Tracking-Id
