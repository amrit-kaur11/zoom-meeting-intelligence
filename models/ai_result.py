import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class AIResult(Base):
    __tablename__ = "ai_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id"), nullable=False, unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    tasks_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string list
    updates_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string list
    raw_aggregated_transcript: Mapped[str] = mapped_column(Text, nullable=True)
    prompt_used: Mapped[str] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="ai_result")
