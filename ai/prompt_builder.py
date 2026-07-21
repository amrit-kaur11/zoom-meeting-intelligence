from typing import List
from utils.config import settings

SYSTEM_PROMPT = """You are an expert AI meeting assistant.
Your task is to analyze the provided Zoom meeting transcript and return a strict JSON object containing:
1. "summary": A concise yet comprehensive executive summary of the meeting.
2. "tasks": A list of clear, actionable tasks or action items identified in the meeting (with assignees if mentioned).
3. "updates": A list of key bullet-point project or status updates.

You MUST respond strictly with valid JSON conforming to the following structure:
{
  "summary": "High-level summary here...",
  "tasks": ["Task 1 description", "Task 2 description"],
  "updates": ["Update 1 bullet", "Update 2 bullet"]
}
Do not add markdown formatting outside the JSON block. Do not include extra conversational text.
"""


class PromptBuilder:
    @staticmethod
    def build_meeting_prompt(transcript: str, topic: str = "Zoom Meeting") -> str:
        return f"{SYSTEM_PROMPT}\n\nMeeting Topic: {topic}\n\nTranscript:\n{transcript}\n\nJSON Output:"

    @staticmethod
    def chunk_transcript(transcript: str, max_words: int = None) -> List[str]:
        """Splits a long transcript into chunks of max_words for Map-Reduce processing."""
        if max_words is None:
            max_words = settings.MAX_TOKEN_CHUNK_WORDS
            
        words = transcript.split()
        if len(words) <= max_words:
            return [transcript]

        chunks = []
        lines = transcript.splitlines()
        current_chunk = []
        current_word_count = 0

        for line in lines:
            line_words = len(line.split())
            if current_word_count + line_words > max_words and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_word_count = line_words
            else:
                current_chunk.append(line)
                current_word_count += line_words

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    @staticmethod
    def build_chunk_summary_prompt(chunk_text: str, chunk_index: int, total_chunks: int) -> str:
        return f"""Summarize part {chunk_index + 1} of {total_chunks} of a long meeting transcript. Extract key points, tasks, and status updates.

Transcript Part:
{chunk_text}
"""

    @staticmethod
    def build_reduce_prompt(chunk_summaries: List[str], topic: str = "Zoom Meeting") -> str:
        combined_summaries = "\n---\n".join(chunk_summaries)
        return f"{SYSTEM_PROMPT}\n\nMeeting Topic: {topic}\n\nThe following are section summaries of a long meeting:\n{combined_summaries}\n\nCombine these into a single unified JSON Output:"
