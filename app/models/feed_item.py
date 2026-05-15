from app.database.connection import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import relationship

class MessageTypeEnum(str, enum.Enum):
    comment = "comment"
    match_event = "match_event"


class FeedItem(Base):
    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(Enum(MessageTypeEnum), nullable=False)
    content = Column(String, nullable=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=True)
    match_id = Column(Integer, ForeignKey("match.id", ondelete="CASCADE"), nullable=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    player = relationship("Player", foreign_keys=[player_id])
    match = relationship("Match", foreign_keys=[match_id])
