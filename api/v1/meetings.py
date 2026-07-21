import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from services.meeting_service import MeetingService
from workers.meeting_processor import MeetingProcessor
from schemas.meeting import MeetingResponse, ProcessMeetingRequest
from schemas.ai import AIResultResponse
from models.meeting import Meeting

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def format_meeting_response(meeting: Meeting) -> MeetingResponse:
    ai_res_dict = None
    if meeting.ai_result:
        ai_res_dict = AIResultResponse(
            id=meeting.ai_result.id,
            meeting_id=meeting.ai_result.meeting_id,
            summary=meeting.ai_result.summary,
            tasks=json.loads(meeting.ai_result.tasks_json or "[]"),
            updates=json.loads(meeting.ai_result.updates_json or "[]"),
            word_count=meeting.ai_result.word_count,
            raw_aggregated_transcript=meeting.ai_result.raw_aggregated_transcript or ""
        )
    return MeetingResponse(
        id=meeting.id,
        zoom_meeting_id=meeting.zoom_meeting_id,
        topic=meeting.topic,
        status=meeting.status,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        active_participants=meeting.active_participants,
        total_participants_joined=meeting.total_participants_joined,
        error_message=meeting.error_message,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        ai_result=ai_res_dict
    )


@router.get("", response_model=List[MeetingResponse])
async def list_meetings(db: AsyncSession = Depends(get_db)):
    """Lists all tracked Zoom meetings and their current processing status."""
    meeting_service = MeetingService(db)
    meetings = await meeting_service.list_meetings()
    return [format_meeting_response(m) for m in meetings]


@router.get("/{zoom_meeting_id}", response_model=MeetingResponse)
async def get_meeting(zoom_meeting_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves specific meeting state and generated AI intelligence."""
    meeting_service = MeetingService(db)
    meeting = await meeting_service.get_meeting_details(zoom_meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")
    return format_meeting_response(meeting)


@router.post("/process", response_model=MeetingResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_meeting_manually(
    req: ProcessMeetingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually triggers VTT transcript fetching & AI processing pipeline.
    """
    meeting_service = MeetingService(db)
    meeting = await meeting_service.get_or_create_meeting(req.zoom_meeting_id, req.topic)

    background_tasks.add_task(
        MeetingProcessor.run_pipeline,
        meeting_id=meeting.id,
        vtt_urls=req.vtt_urls,
        topic=meeting.topic
    )

    await db.refresh(meeting)
    return format_meeting_response(meeting)


@router.post("/{meeting_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_meeting_ai(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Failure Recovery Endpoint:
    Retries AI processing directly from stored VTT transcripts in DB without re-downloading!
    """
    meeting_service = MeetingService(db)
    meeting = await meeting_service.meeting_repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found.")

    background_tasks.add_task(MeetingProcessor.retry_ai_processing, meeting_id=meeting.id)
    return {"status": "accepted", "message": f"Retry initiated for meeting {meeting_id}."}
