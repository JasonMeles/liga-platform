from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database.connection import Base
import enum

class MatchState(str, enum.Enum):
    pending = "PENDING"
    in_progress = "IN_PROGRESS"
    finished = "FINISHED"

class Match(Base):
    __tablename__ = "match"

    id = Column(Integer, primary_key=True, index=True)
    team_home_id = Column(Integer, ForeignKey("equipes.id", ondelete="CASCADE"), nullable=False)
    team_away_id = Column(Integer, ForeignKey("equipes.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    score_home = Column(Integer, nullable=True)
    score_away = Column(Integer, nullable=True)
    state = Column(Enum(MatchState), nullable=False, default=MatchState.pending)
    scheduled_at = Column(DateTime, nullable=True)