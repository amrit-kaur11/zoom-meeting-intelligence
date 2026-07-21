import asyncio
import json
import httpx
from typing import Optional, List
from utils.config import settings
from utils.logger import logger
from ai.prompt_builder import PromptBuilder
from ai.json_parser import JSONParser
from schemas.ai import AIIntelligenceOutput


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER

    async def _call_llm_api(self, prompt: str) -> str:
        """Invokes external LLM API (Groq Cloud / xAI Grok / OpenAI) or Mock LLM with retries."""
        max_retries = 3
        backoff = 1.0

        # Auto-detect Groq key format (starts with gsk_) even if provider is set to grok
        groq_key = settings.GROQ_API_KEY or (settings.GROK_API_KEY if settings.GROK_API_KEY.startswith("gsk_") else "")
        grok_key = settings.GROK_API_KEY if not settings.GROK_API_KEY.startswith("gsk_") else ""

        for attempt in range(1, max_retries + 1):
            try:
                # Groq Cloud API (Super fast Llama 3 models)
                if (self.provider == "groq" or self.provider == "grok") and groq_key:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": settings.GROQ_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    }
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code >= 400:
                            logger.error(f"Groq API Error Response Body: {resp.text}")
                        resp.raise_for_status()
                        result = resp.json()
                        return result['choices'][0]['message']['content']

                # xAI Grok API
                elif self.provider == "grok" and grok_key:
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {grok_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": settings.GROK_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    }
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code >= 400:
                            logger.error(f"xAI Grok API Error Response Body: {resp.text}")
                        resp.raise_for_status()
                        result = resp.json()
                        return result['choices'][0]['message']['content']

                # OpenAI API
                elif self.provider == "openai" and settings.OPENAI_API_KEY:
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    }
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                        if resp.status_code >= 400:
                            logger.error(f"OpenAI API Error Response Body: {resp.text}")
                        resp.raise_for_status()
                        result = resp.json()
                        return result['choices'][0]['message']['content']

                else:
                    # Mock LLM provider fallback
                    logger.info("No active API keys found. Falling back to Mock LLM provider.")
                    return self._generate_mock_response(prompt)

            except Exception as e:
                logger.warning(f"LLM API Call Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    raise e
                await asyncio.sleep(backoff)
                backoff *= 2.0

        raise RuntimeError("LLM retries exhausted.")

    def _generate_mock_response(self, prompt: str) -> str:
        """Generates dynamic realistic JSON output for test environment."""
        lines = [line for line in prompt.splitlines() if line.strip() and ":" in line and not line.startswith("http")]
        speakers = list(set([line.split(":")[0].strip("[]0123456789 ") for line in lines[:10]]))
        speaker_str = ", ".join(speakers) if speakers else "Team members"

        mock_data = {
            "summary": f"The meeting covered project status, backend architecture, and workflow optimizations with {speaker_str}. Core technical decisions were agreed upon, including webhook idempotency, VTT aggregation, and background retry pipelines.",
            "tasks": [
                "Deploy FastAPI webhook listener to staging environment",
                "Implement VTT timestamp deduplication for fragmented recordings",
                "Configure background worker task retry mechanisms for LLM processing"
            ],
            "updates": [
                "Webhook endpoint idempotency validation completed successfully",
                "VTT regex parser integrated into transcript aggregation pipeline",
                "AI meeting intelligence schema validated against Pydantic models"
            ]
        }
        return json.dumps(mock_data)

    async def generate_intelligence(self, transcript: str, topic: str = "Zoom Meeting") -> AIIntelligenceOutput:
        """
        Main entry point for generating meeting intelligence using LLM.
        Applies token chunking (Map-Reduce) if transcript exceeds threshold.
        """
        chunks = PromptBuilder.chunk_transcript(transcript)

        if len(chunks) == 1:
            prompt = PromptBuilder.build_meeting_prompt(transcript, topic)
            raw_response = await self._call_llm_api(prompt)
            return JSONParser.parse_llm_json(raw_response)
        else:
            logger.info(f"Transcript contains {len(chunks)} chunks. Executing Map-Reduce LLM processing...")
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                chunk_prompt = PromptBuilder.build_chunk_summary_prompt(chunk, idx, len(chunks))
                summary_part = await self._call_llm_api(chunk_prompt)
                chunk_summaries.append(summary_part)

            reduce_prompt = PromptBuilder.build_reduce_prompt(chunk_summaries, topic)
            final_raw = await self._call_llm_api(reduce_prompt)
            return JSONParser.parse_llm_json(final_raw)
