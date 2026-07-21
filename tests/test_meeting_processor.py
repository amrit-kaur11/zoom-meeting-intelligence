import pytest
from database.session import AsyncSessionLocal, init_db
from services.meeting_service import MeetingService
from workers.meeting_processor import MeetingProcessor
from models.meeting import MeetingStatus


@pytest.mark.asyncio
async def test_end_to_end_processor_and_retry():
    await init_db()
    async with AsyncSessionLocal() as db:
        meeting_service = MeetingService(db)
        meeting = await meeting_service.get_or_create_meeting("555444333", "E2E Test Meeting")
        meeting_id = meeting.id

    # Run complete background pipeline
    vtt_urls = ["mock://zoom.us/rec/1.vtt", "mock://zoom.us/rec/2.vtt"]
    await MeetingProcessor.run_pipeline(meeting_id, vtt_urls, "E2E Test Meeting")

    # Verify status completed and AI result saved
    async with AsyncSessionLocal() as db:
        meeting_service = MeetingService(db)
        updated_meeting = await meeting_service.get_meeting_details("555444333")
        assert updated_meeting.status == MeetingStatus.COMPLETED
        assert updated_meeting.ai_result is not None
        assert len(updated_meeting.ai_result.summary) > 0

    # Test failure recovery retry using stored transcript without re-downloading
    await MeetingProcessor.retry_ai_processing(meeting_id)

    async with AsyncSessionLocal() as db:
        meeting_service = MeetingService(db)
        retried_meeting = await meeting_service.get_meeting_details("555444333")
        assert retried_meeting.status == MeetingStatus.COMPLETED
        assert retried_meeting.ai_result is not None
