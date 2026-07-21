import hashlib
import json
from typing import Dict, Any, Tuple, Optional, List
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.webhook_repository import WebhookRepository
from services.meeting_service import MeetingService
from workers.meeting_processor import MeetingProcessor
from models.meeting import MeetingStatus
from utils.logger import logger


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.webhook_repo = WebhookRepository(db)
        self.meeting_service = MeetingService(db)

    def generate_event_id(self, payload: Dict[str, Any], header_event_id: Optional[str] = None) -> str:
        """Generates or extracts a deterministic unique event_id for idempotency checking."""
        if header_event_id:
            return header_event_id
        if payload.get("event_id"):
            return payload["event_id"]
            
        # Fallback hash of event type + zoom meeting id + event_ts
        event_type = payload.get("event", "unknown")
        event_ts = payload.get("event_ts", "")
        obj = payload.get("payload", {}).get("object", {})
        zoom_id = obj.get("id") or obj.get("uuid") or "global"
        
        raw_str = f"{event_type}_{zoom_id}_{event_ts}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    async def handle_webhook(
        self, payload: Dict[str, Any], header_event_id: Optional[str], background_tasks: BackgroundTasks
    ) -> Tuple[bool, str]:
        """
        Process Zoom webhook payload:
        1. Check idempotency (duplicate event_id)
        2. Update meeting lifecycle and participant counters
        3. Enqueue background processor on meeting completion
        """
        event_id = self.generate_event_id(payload, header_event_id)
        
        # Idempotency check
        existing_event = await self.webhook_repo.get_by_event_id(event_id)
        if existing_event:
            logger.info(f"Duplicate webhook event detected (event_id: {event_id}). Skipping.")
            return True, "Duplicate event ignored."

        event_type = payload.get("event", "unknown_event")
        zoom_payload = payload.get("payload", {})
        obj = zoom_payload.get("object", {})
        zoom_meeting_id = str(obj.get("id") or obj.get("uuid") or "")

        # Record webhook event in DB
        await self.webhook_repo.create_event(
            event_id=event_id,
            event_type=event_type,
            zoom_meeting_id=zoom_meeting_id if zoom_meeting_id else None,
            payload=payload
        )

        if not zoom_meeting_id:
            return True, "Webhook logged without meeting ID."

        topic = obj.get("topic", f"Meeting {zoom_meeting_id}")
        meeting = await self.meeting_service.get_or_create_meeting(zoom_meeting_id, topic)

        # Webhook Event State Machine Routing
        if event_type in ["meeting.started", "meeting.participant_joined"]:
            meeting.active_participants += 1
            meeting.total_participants_joined += 1
            meeting.status = MeetingStatus.ACTIVE
            await self.db.commit()
            logger.info(f"Meeting {zoom_meeting_id}: Participant joined (active: {meeting.active_participants}). State: ACTIVE.")

        elif event_type == "meeting.participant_left":
            meeting.active_participants = max(0, meeting.active_participants - 1)
            await self.db.commit()
            logger.info(f"Meeting {zoom_meeting_id}: Participant left (active: {meeting.active_participants}).")

        elif event_type in ["meeting.ended", "recording.completed"]:
            meeting.status = MeetingStatus.ENDED
            await self.db.commit()
            logger.info(f"Meeting {zoom_meeting_id}: Meeting ended. Collecting VTT transcripts...")

            # Extract VTT download URLs from recording files
            vtt_urls: List[str] = []
            recording_files = obj.get("recording_files", [])
            for rf in recording_files:
                file_type = (rf.get("file_type") or rf.get("file_extension") or "").upper()
                if file_type in ["TRANSCRIPT", "VTT"]:
                    url = rf.get("download_url")
                    if url:
                        vtt_urls.append(url)

            # Fallback mock VTT URL for testing if Zoom payload didn't include recording links
            if not vtt_urls:
                vtt_urls = [f"mock://zoom.us/rec/vtt/{zoom_meeting_id}_1.vtt"]

            # Enqueue non-blocking background processing
            background_tasks.add_task(
                MeetingProcessor.run_pipeline,
                meeting_id=meeting.id,
                vtt_urls=vtt_urls,
                topic=meeting.topic
            )
            logger.info(f"Meeting {zoom_meeting_id}: Background pipeline enqueued with {len(vtt_urls)} VTT files.")

        return True, "Webhook processed successfully."
