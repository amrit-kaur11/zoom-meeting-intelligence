# Zoom Meeting Intelligence & Reconstruction System

AI-powered FastAPI backend that processes Zoom webhooks, aggregates
WebVTT transcripts, and generates structured meeting intelligence using
Grok-2-Latest.

## Overview

This backend follows a clean, event-driven architecture. Zoom webhooks
are acknowledged immediately, while transcript parsing and AI processing
execute asynchronously using FastAPI BackgroundTasks.

## Features

-   FastAPI REST APIs
-   Zoom Webhook Processing
-   Async SQLAlchemy + SQLite
-   HTTPX AsyncClient
-   WebVTT Transcript Parsing
-   Grok-2-Latest Integration
-   Structured JSON via Pydantic
-   Repository & Service Pattern
-   Swagger UI
-   Pytest

## Architecture

``` text
Zoom
 -> Webhook API
 -> Webhook Service
 -> Meeting Repository
 -> Background Worker
 -> Transcript Parser
 -> Prompt Builder
 -> Grok API
 -> JSON Parser
 -> SQLite
```

## Tech Stack

-   Python 3.13
-   FastAPI
-   SQLAlchemy Async
-   SQLite
-   Pydantic v2
-   HTTPX
-   Grok-2-Latest
-   Pytest

## Supported Events

-   meeting.started
-   meeting.participant_joined
-   meeting.participant_left
-   meeting.ended
-   recording.completed

## Installation

``` bash
git clone https://github.com/amrit-kaur11/zoom-meeting-intelligence.git
cd zoom-meeting-intelligence
python -m venv venv
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment

``` env
DATABASE_URL=sqlite+aiosqlite:///./zoom_intelligence.db
LLM_PROVIDER=grok
GROK_MODEL=grok-2-latest
GROK_API_KEY=YOUR_KEY
```

## AI Output

``` json
{
 "summary":"...",
 "tasks":["..."],
 "updates":["..."]
}
```

## Future Improvements

-   Celery + Redis
-   Zoom OAuth
-   HMAC Signature Verification
-   WebSockets
-   PostgreSQL

## Author

Amrit Kaur GitHub: https://github.com/amrit-kaur11
