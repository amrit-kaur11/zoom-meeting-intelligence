import pytest
from ai.prompt_builder import PromptBuilder
from ai.json_parser import JSONParser
from ai.llm_client import LLMClient


def test_json_parser_clean():
    raw_json = '{"summary": "Test summary", "tasks": ["Task 1"], "updates": ["Update 1"]}'
    output = JSONParser.parse_llm_json(raw_json)
    assert output.summary == "Test summary"
    assert output.tasks == ["Task 1"]
    assert output.updates == ["Update 1"]


def test_json_parser_markdown_fence():
    raw_markdown = """```json
{
  "summary": "Markdown summary",
  "tasks": ["Task A", "Task B"],
  "updates": ["Update X"]
}
```"""
    output = JSONParser.parse_llm_json(raw_markdown)
    assert output.summary == "Markdown summary"
    assert len(output.tasks) == 2


def test_transcript_chunking_strategy():
    long_transcript = "\n".join([f"Line {i}: [00:00:{i:02d}] Speaker: Spoken word content here." for i in range(100)])
    # Set small word threshold to test split
    chunks = PromptBuilder.chunk_transcript(long_transcript, max_words=50)
    assert len(chunks) > 1


@pytest.mark.asyncio
async def test_llm_client_mock_generation():
    client = LLMClient(provider="mock")
    output = await client.generate_intelligence("Alice: Let's optimize database indexes.", "Database Meeting")
    assert output.summary is not None
    assert len(output.tasks) > 0
    assert len(output.updates) > 0
