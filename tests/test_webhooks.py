import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_webhook_fast_ack_and_idempotency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "event": "meeting.participant_joined",
            "event_ts": 1600000000,
            "event_id": "test_evt_12345",
            "payload": {
                "object": {
                    "id": "888999111",
                    "topic": "Architecture Sync",
                    "participant": {"user_name": "Dave"}
                }
            }
        }

        # First request - Should succeed
        resp1 = await ac.post("/api/v1/webhooks/zoom", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "success"

        # Duplicate request - Idempotency should intercept and ignore duplicate
        resp2 = await ac.post("/api/v1/webhooks/zoom", json=payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "Duplicate event ignored" in data2["message"]


@pytest.mark.asyncio
async def test_meeting_lifecycle_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger meeting process manually
        req = {
            "zoom_meeting_id": "777666555",
            "topic": "Sprint Planning",
            "vtt_urls": ["mock://test_vtt_1.vtt"]
        }
        resp = await ac.post("/api/v1/meetings/process", json=req)
        assert resp.status_code == 202
        meeting = resp.json()
        assert meeting["zoom_meeting_id"] == "777666555"

        # Query meeting list
        list_resp = await ac.get("/api/v1/meetings")
        assert list_resp.status_code == 200
        meetings = list_resp.json()
        assert len(meetings) >= 1
