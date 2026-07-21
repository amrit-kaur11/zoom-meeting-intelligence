from fastapi import APIRouter
from api.v1.webhooks import router as webhooks_router
from api.v1.meetings import router as meetings_router

api_router = APIRouter()
api_router.include_router(webhooks_router)
api_router.include_router(meetings_router)
