import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class MeetingStatus(str, enum.Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    AGGREGATING = "AGGREGATING"
    AI_PROCESSING = "AI_PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zoom_meeting_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus), default=MeetingStatus.CREATED, nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    active_participants: Mapped[int] = mapped_column(Integer, default=0)
    total_participants_joined: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transcript_files = relationship("TranscriptFile", back_populates="meeting", cascade="all, delete-orphan")
    ai_result = relationship("AIResult", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
