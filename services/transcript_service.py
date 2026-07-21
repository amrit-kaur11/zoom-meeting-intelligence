import httpx
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.transcript_repository import TranscriptRepository
from parser.vtt_parser import VTTParser
from models.transcript_file import TranscriptFileStatus
from utils.logger import logger


class TranscriptService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TranscriptRepository(db)

    async def fetch_vtt_content(self, url: str) -> str:
        """Fetches raw VTT content over HTTP or returns mock VTT if mock URL/offline."""
        if url.startswith("mock://") or not url.startswith("http"):
            # Return realistic sample VTT for local test URLs
            return """WEBVTT

00:00:01.000 --> 00:00:05.000
<v Alice>Hello everyone, let's start the Zoom architectural meeting.

00:00:06.000 --> 00:00:10.000
<v Bob>Hi Alice, I will work on the FastAPI backend and database models.

00:00:11.000 --> 00:00:15.000
<v Charlie>I will handle the VTT transcript parser and AI pipeline integration.
"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text
        except Exception as e:
            logger.error(f"Failed to fetch VTT from URL {url}: {e}")
            raise e

    async def fetch_and_aggregate_transcripts(self, meeting_id: str, file_urls: List[str]) -> Tuple[str, List[str]]:
        """
        Downloads all provided VTT URLs, parses each VTT fragment, updates DB,
        and aggregates into a single clean 'Speaker: Text' transcript.
        """
        raw_vtt_list: List[str] = []

        # Ensure transcript files are registered in DB
        db_files = await self.repository.get_by_meeting_id(meeting_id)
        if not db_files:
            db_files = await self.repository.add_transcript_files(meeting_id, file_urls)

        for tf in db_files:
            try:
                # If already downloaded & parsed in DB (e.g. from previous run before LLM retry), reuse!
                if tf.raw_vtt_content and tf.status == TranscriptFileStatus.PARSED:
                    raw_vtt_list.append(tf.raw_vtt_content)
                    continue

                raw_vtt = await self.fetch_vtt_content(tf.file_url)
                parsed_cues = VTTParser.parse_single_vtt(raw_vtt)
                clean_part = "\n".join([f"[{c.start_time_str}] {c.speaker}: {c.text}" for c in parsed_cues])

                await self.repository.update_transcript_content(
                    transcript_id=tf.id,
                    raw_vtt=raw_vtt,
                    parsed_content=clean_part,
                    status=TranscriptFileStatus.PARSED
                )
                raw_vtt_list.append(raw_vtt)

            except Exception as e:
                logger.error(f"Error processing transcript file {tf.file_url}: {e}")
                await self.repository.update_transcript_content(
                    transcript_id=tf.id,
                    raw_vtt="",
                    parsed_content="",
                    status=TranscriptFileStatus.FAILED
                )

        if not raw_vtt_list:
            raise ValueError("No transcript files could be downloaded or parsed.")

        # Aggregate across all files (deduplicating overlapping segments across pause/resumes)
        aggregated_transcript = VTTParser.format_to_clean_text(raw_vtt_list)
        return aggregated_transcript, raw_vtt_list
