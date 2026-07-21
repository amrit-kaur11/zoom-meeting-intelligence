import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.ai_result import AIResult


class AIRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_meeting_id(self, meeting_id: str) -> Optional[AIResult]:
        result = await self.db.execute(
            select(AIResult).where(AIResult.meeting_id == meeting_id)
        )
        return result.scalars().first()

    async def save_ai_result(
        self,
        meeting_id: str,
        summary: str,
        tasks: List[str],
        updates: List[str],
        raw_aggregated_transcript: str,
        prompt_used: Optional[str] = None
    ) -> AIResult:
        word_count = len(raw_aggregated_transcript.split()) if raw_aggregated_transcript else 0
        
        # Check if exists (for retry updates)
        existing = await self.get_by_meeting_id(meeting_id)
        if existing:
            existing.summary = summary
            existing.tasks_json = json.dumps(tasks)
            existing.updates_json = json.dumps(updates)
            existing.raw_aggregated_transcript = raw_aggregated_transcript
            existing.prompt_used = prompt_used
            existing.word_count = word_count
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
            
        ai_result = AIResult(
            meeting_id=meeting_id,
            summary=summary,
            tasks_json=json.dumps(tasks),
            updates_json=json.dumps(updates),
            raw_aggregated_transcript=raw_aggregated_transcript,
            prompt_used=prompt_used,
            word_count=word_count
        )
        self.db.add(ai_result)
        await self.db.commit()
        await self.db.refresh(ai_result)
        return ai_result
