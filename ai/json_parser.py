import json
import re
from typing import Dict, Any
from schemas.ai import AIIntelligenceOutput
from utils.logger import logger


class JSONParser:
    @staticmethod
    def parse_llm_json(llm_response: str) -> AIIntelligenceOutput:
        """
        Parses LLM string output into AIIntelligenceOutput schema.
        Handles markdown block wrapping ```json ... ``` and raw JSON text.
        """
        cleaned = llm_response.strip()

        # Remove markdown code fence if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)
        else:
            # Look for outer braces if any extra text exists
            brace_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if brace_match:
                cleaned = brace_match.group(0)

        try:
            data: Dict[str, Any] = json.loads(cleaned)
            return AIIntelligenceOutput(
                summary=data.get("summary", "No summary provided."),
                tasks=data.get("tasks", []) if isinstance(data.get("tasks"), list) else [],
                updates=data.get("updates", []) if isinstance(data.get("updates"), list) else []
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON output: {e}. Raw response: {llm_response}")
            # Robust fallback structure if json.loads fails
            return AIIntelligenceOutput(
                summary=f"Raw Output: {llm_response[:300]}...",
                tasks=["Parsing error encountered. Review raw log."],
                updates=["AI response could not be formatted as strict JSON."]
            )
