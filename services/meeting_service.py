from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.meeting_repository import MeetingRepository
from models.meeting import Meeting, MeetingStatus


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.meeting_repo = MeetingRepository(db)

    async def get_or_create_meeting(self, zoom_meeting_id: str, topic: Optional[str] = None) -> Meeting:
        meeting = await self.meeting_repo.get_by_zoom_id(zoom_meeting_id)
        if not meeting:
            meeting = await self.meeting_repo.create_meeting(zoom_meeting_id=zoom_meeting_id, topic=topic)
        return meeting

    async def transition_status(self, meeting_id: str, new_status: MeetingStatus, error_msg: Optional[str] = None) -> Meeting:
        return await self.meeting_repo.update_status(meeting_id, new_status, error_msg)

    async def get_meeting_details(self, zoom_meeting_id: str) -> Optional[Meeting]:
        return await self.meeting_repo.get_by_zoom_id(zoom_meeting_id)

    async def list_meetings(self) -> Sequence[Meeting]:
        return await self.meeting_repo.get_all()
