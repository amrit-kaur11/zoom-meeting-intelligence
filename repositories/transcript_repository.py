from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.transcript_file import TranscriptFile, TranscriptFileStatus


class TranscriptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_transcript_files(self, meeting_id: str, file_urls: List[str]) -> List[TranscriptFile]:
        created_files = []
        for idx, url in enumerate(file_urls):
            tf = TranscriptFile(
                meeting_id=meeting_id,
                file_url=url,
                file_order=idx,
                status=TranscriptFileStatus.PENDING
            )
            self.db.add(tf)
            created_files.append(tf)
        await self.db.commit()
        for tf in created_files:
            await self.db.refresh(tf)
        return created_files

    async def get_by_meeting_id(self, meeting_id: str) -> Sequence[TranscriptFile]:
        result = await self.db.execute(
            select(TranscriptFile)
            .where(TranscriptFile.meeting_id == meeting_id)
            .order_by(TranscriptFile.file_order.asc())
        )
        return result.scalars().all()

    async def update_transcript_content(
        self, transcript_id: str, raw_vtt: str, parsed_content: str, status: TranscriptFileStatus
    ) -> TranscriptFile:
        result = await self.db.execute(
            select(TranscriptFile).where(TranscriptFile.id == transcript_id)
        )
        tf = result.scalars().first()
        if tf:
            tf.raw_vtt_content = raw_vtt
            tf.parsed_content = parsed_content
            tf.status = status
            await self.db.commit()
            await self.db.refresh(tf)
        return tf
