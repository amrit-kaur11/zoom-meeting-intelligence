from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/zoom", status_code=status.HTTP_200_OK)
async def handle_zoom_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    x_zm_tracking_id: Optional[str] = Header(None, alias="X-Zm-Tracking-Id"),
    db: AsyncSession = Depends(get_db)
):
    """
    Zoom Webhook Endpoint.
    Responds immediately (< 50ms) to ensure Zoom fast ACK requirement.
    Idempotent processing via tracking event IDs.
    """
    webhook_service = WebhookService(db)
    success, message = await webhook_service.handle_webhook(
        payload=payload,
        header_event_id=x_zm_tracking_id,
        background_tasks=background_tasks
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success" if success else "failed", "message": message}
    )
