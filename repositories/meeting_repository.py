from typing import Optional, Sequence
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.meeting import Meeting, MeetingStatus


class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_zoom_id(self, zoom_meeting_id: str) -> Optional[Meeting]:
        result = await self.db.execute(
            select(Meeting)
            .options(selectinload(Meeting.transcript_files), selectinload(Meeting.ai_result))
            .where(Meeting.zoom_meeting_id == zoom_meeting_id)
        )
        return result.scalars().first()

    async def get_by_id(self, meeting_id: str) -> Optional[Meeting]:
        result = await self.db.execute(
            select(Meeting)
            .options(selectinload(Meeting.transcript_files), selectinload(Meeting.ai_result))
            .where(Meeting.id == meeting_id)
        )
        return result.scalars().first()

    async def get_all(self, limit: int = 100) -> Sequence[Meeting]:
        result = await self.db.execute(
            select(Meeting)
            .options(selectinload(Meeting.transcript_files), selectinload(Meeting.ai_result))
            .order_by(Meeting.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_meeting(self, zoom_meeting_id: str, topic: Optional[str] = None) -> Meeting:
        meeting = Meeting(
            zoom_meeting_id=zoom_meeting_id,
            topic=topic or f"Meeting {zoom_meeting_id}",
            status=MeetingStatus.CREATED,
            start_time=datetime.utcnow()
        )
        self.db.add(meeting)
        await self.db.commit()
        # Return fully loaded meeting
        return await self.get_by_id(meeting.id)

    async def update_status(self, meeting_id: str, status: MeetingStatus, error_message: Optional[str] = None) -> Meeting:
        meeting = await self.get_by_id(meeting_id)
        if meeting:
            meeting.status = status
            meeting.updated_at = datetime.utcnow()
            if error_message:
                meeting.error_message = error_message
            await self.db.commit()
            return await self.get_by_id(meeting_id)
        return meeting
