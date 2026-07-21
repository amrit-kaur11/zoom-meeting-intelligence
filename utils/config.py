import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Zoom Meeting Intelligence & Reconstruction System"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./zoom_intelligence.db"
    
    # Webhook
    ZOOM_WEBHOOK_SECRET_TOKEN: str = "test_webhook_secret"
    
    # LLM Settings (Groq / xAI / OpenAI)
    LLM_PROVIDER: str = "groq"  # Options: 'groq', 'grok', 'mock', 'openai'
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # High performance Groq model
    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-2"
    OPENAI_API_KEY: str = ""
    MAX_TOKEN_CHUNK_WORDS: int = 2000  # Token limit strategy split threshold in words
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
