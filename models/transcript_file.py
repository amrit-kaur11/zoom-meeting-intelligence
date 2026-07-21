import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class TranscriptFileStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOWNLOADED = "DOWNLOADED"
    PARSED = "PARSED"
    FAILED = "FAILED"


class TranscriptFile(Base):
    __tablename__ = "transcript_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=True)
    raw_vtt_content: Mapped[str] = mapped_column(Text, nullable=True)
    parsed_content: Mapped[str] = mapped_column(Text, nullable=True)
    file_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[TranscriptFileStatus] = mapped_column(
        Enum(TranscriptFileStatus), default=TranscriptFileStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="transcript_files")
