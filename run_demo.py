import asyncio
from database.session import init_db, AsyncSessionLocal
from services.meeting_service import MeetingService
from workers.meeting_processor import MeetingProcessor
from utils.logger import logger


async def main():
    logger.info("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        meeting_service = MeetingService(db)
        meeting = await meeting_service.get_or_create_meeting(
            zoom_meeting_id="999888777",
            topic="Quarterly Product & AI Architecture Review"
        )
        meeting_id = meeting.id

    vtt_sample_1 = """WEBVTT

00:00:01.000 --> 00:00:06.000
<v Sarah>Good morning team! Let's kick off the Zoom Intelligence integration review.

00:00:07.000 --> 00:00:12.000
<v Mark>Thanks Sarah. We have deployed the webhook receiver and verified idempotency.

00:00:13.000 --> 00:00:18.000
<v Sarah>Great. Mark, please ensure the VTT parser handles pause/resume overlapping timestamps properly.

00:00:19.000 --> 00:00:25.000
<v Mark>Will do. I will complete the VTT deduplication testing by tomorrow end of day.
"""

    vtt_sample_2 = """WEBVTT

00:00:26.000 --> 00:00:32.000
<v Elena>Regarding the LLM integration, we switched the provider to xAI Grok (grok-2-latest).

00:00:33.000 --> 00:00:40.000
<v Sarah>Awesome. Elena, please make sure Map-Reduce token chunking handles 3-hour long transcripts.

00:00:41.000 --> 00:00:48.000
<v Elena>I've implemented the chunking strategy. I'll monitor rate limits and retry pipelines.
"""

    from unittest.mock import patch
    from services.transcript_service import TranscriptService

    original_fetch = TranscriptService.fetch_vtt_content

    async def mock_fetch(self, url: str) -> str:
        if "part1" in url:
            return vtt_sample_1
        elif "part2" in url:
            return vtt_sample_2
        return await original_fetch(self, url)

    with patch.object(TranscriptService, "fetch_vtt_content", mock_fetch):
        logger.info("Executing Meeting Processor Pipeline with Grok API...")
        await MeetingProcessor.run_pipeline(
            meeting_id=meeting_id,
            vtt_urls=["http://zoom.us/rec/part1.vtt", "http://zoom.us/rec/part2.vtt"],
            topic="Quarterly Product & AI Architecture Review"
        )

    # Fetch and print final results
    async with AsyncSessionLocal() as db:
        meeting_service = MeetingService(db)
        final_meeting = await meeting_service.get_meeting_details("999888777")
        print("\n" + "="*60)
        print("FINAL DEMO RESULT FROM GROK LLM PIPELINE")
        print("="*60)
        print(f"Meeting Topic  : {final_meeting.topic}")
        print(f"Status         : {final_meeting.status}")
        if final_meeting.ai_result:
            import json
            print(f"\nSUMMARY:\n{final_meeting.ai_result.summary}\n")
            print(f"TASKS:\n" + "\n".join([f"  * {t}" for t in json.loads(final_meeting.ai_result.tasks_json)]))
            print(f"\nUPDATES:\n" + "\n".join([f"  * {u}" for u in json.loads(final_meeting.ai_result.updates_json)]))
            print(f"\nAGGREGATED TRANSCRIPT:\n{final_meeting.ai_result.raw_aggregated_transcript}")
        else:
            print(f"Error Message  : {final_meeting.error_message}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
