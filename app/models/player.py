from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    hashed_password = Column(String, nullable=False)




class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    token      = Column(String, unique=True, nullable=False, index=True)
    player_id  = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LeagueRoleEnum(str, enum.Enum):
    manager = "manager"
    membre = "membre"

class League(Base):
    __tablename__ = "leagues"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PlayerLeague(Base):
    __tablename__ = "player_leagues"

    id        = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    role      = Column(Enum(LeagueRoleEnum), nullable=False, default=LeagueRoleEnum.membre)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())