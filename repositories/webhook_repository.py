import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.webhook_event import WebhookEvent


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_event_id(self, event_id: str) -> Optional[WebhookEvent]:
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        return result.scalars().first()

    async def create_event(self, event_id: str, event_type: str, zoom_meeting_id: Optional[str], payload: dict) -> WebhookEvent:
        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            zoom_meeting_id=zoom_meeting_id,
            payload=json.dumps(payload),
            processed=True
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
