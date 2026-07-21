import traceback
from typing import List, Optional
from database.session import AsyncSessionLocal
from services.meeting_service import MeetingService
from services.transcript_service import TranscriptService
from repositories.ai_repository import AIRepository
from repositories.transcript_repository import TranscriptRepository
from models.meeting import MeetingStatus
from ai.llm_client import LLMClient
from utils.logger import logger


class MeetingProcessor:
    @staticmethod
    async def run_pipeline(meeting_id: str, vtt_urls: List[str], topic: Optional[str] = "Zoom Meeting"):
        """Background worker pipeline executing VTT aggregation and AI processing."""
        async with AsyncSessionLocal() as db:
            meeting_service = MeetingService(db)
            transcript_service = TranscriptService(db)
            ai_repo = AIRepository(db)
            llm_client = LLMClient()

            try:
                # Step 1: Transition to AGGREGATING
                logger.info(f"Meeting {meeting_id}: Starting transcript aggregation...")
                await meeting_service.transition_status(meeting_id, MeetingStatus.AGGREGATING)

                # Step 2: Fetch, parse & aggregate transcripts
                aggregated_transcript, _ = await transcript_service.fetch_and_aggregate_transcripts(
                    meeting_id, vtt_urls
                )
                logger.info(f"Meeting {meeting_id}: Aggregated transcript generated successfully ({len(aggregated_transcript.split())} words).")

                # Step 3: Transition to AI_PROCESSING
                await meeting_service.transition_status(meeting_id, MeetingStatus.AI_PROCESSING)
                logger.info(f"Meeting {meeting_id}: Executing AI LLM processing...")

                # Step 4: Run AI LLM pipeline
                ai_output = await llm_client.generate_intelligence(aggregated_transcript, topic)

                # Step 5: Save AI Results
                await ai_repo.save_ai_result(
                    meeting_id=meeting_id,
                    summary=ai_output.summary,
                    tasks=ai_output.tasks,
                    updates=ai_output.updates,
                    raw_aggregated_transcript=aggregated_transcript
                )

                # Step 6: Transition to COMPLETED
                await meeting_service.transition_status(meeting_id, MeetingStatus.COMPLETED)
                logger.info(f"Meeting {meeting_id}: Pipeline finished successfully! Status set to COMPLETED.")

            except Exception as e:
                err_msg = f"Pipeline execution failed: {str(e)}\n{traceback.format_exc()}"
                logger.error(f"Meeting {meeting_id}: {err_msg}")
                await meeting_service.transition_status(meeting_id, MeetingStatus.FAILED, error_msg=str(e))

    @staticmethod
    async def retry_ai_processing(meeting_id: str):
        """
        Failure Recovery Retry Method:
        Retries AI generation directly from stored transcript files in DB
        without re-downloading or re-combining VTT files!
        """
        async with AsyncSessionLocal() as db:
            meeting_service = MeetingService(db)
            transcript_repo = TranscriptRepository(db)
            ai_repo = AIRepository(db)
            llm_client = LLMClient()

            meeting = await meeting_service.meeting_repo.get_by_id(meeting_id)
            if not meeting:
                logger.error(f"Cannot retry: Meeting {meeting_id} not found.")
                return

            try:
                # Transition directly to AI_PROCESSING
                await meeting_service.transition_status(meeting_id, MeetingStatus.AI_PROCESSING)
                
                # Fetch already stored raw VTT contents from DB
                transcript_files = await transcript_repo.get_by_meeting_id(meeting_id)
                raw_vtts = [tf.raw_vtt_content for tf in transcript_files if tf.raw_vtt_content]

                if not raw_vtts:
                    raise ValueError("No saved VTT content found in DB for retry.")

                from parser.vtt_parser import VTTParser
                aggregated_transcript = VTTParser.format_to_clean_text(raw_vtts)

                # Execute LLM call
                ai_output = await llm_client.generate_intelligence(aggregated_transcript, meeting.topic)

                # Save AI Results
                await ai_repo.save_ai_result(
                    meeting_id=meeting_id,
                    summary=ai_output.summary,
                    tasks=ai_output.tasks,
                    updates=ai_output.updates,
                    raw_aggregated_transcript=aggregated_transcript
                )

                await meeting_service.transition_status(meeting_id, MeetingStatus.COMPLETED)
                logger.info(f"Meeting {meeting_id}: Retry successful! Status set to COMPLETED.")

            except Exception as e:
                logger.error(f"Meeting {meeting_id}: Retry failed: {e}")
                await meeting_service.transition_status(meeting_id, MeetingStatus.FAILED, error_msg=f"Retry error: {str(e)}")
