from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import relationship

class PlayerTypeEnum(str, enum.Enum):
    humain = "humain"
    ia = "ia"

class SportTypeEnum(str, enum.Enum):
    football = "football"
    basketball = "basketball"

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    hashed_password = Column(String, nullable=False)
    player_type = Column(Enum(PlayerTypeEnum), nullable=False, default=PlayerTypeEnum.humain)


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
    max_team = Column(Integer, nullable=False)
    max_per_player = Column(Integer, nullable=False)
    is_active = Column(Boolean, default = False, server_default="false", nullable = False )
    total_journeys = Column(Integer, nullable=False)
    sport_type = Column(Enum(SportTypeEnum), nullable=False, default=SportTypeEnum.football)
    player_leagues = relationship("PlayerLeague")
    @property 
    def manager_username(self) -> str: 
        for i in self.player_leagues:
            if i.role == LeagueRoleEnum.manager: 
                return i.player.username 
        raise ValueError("Cette ligue n'a pas de manager")

class PlayerLeague(Base):
    __tablename__ = "player_leagues"

    id        = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    role      = Column(Enum(LeagueRoleEnum), nullable=False, default=LeagueRoleEnum.membre)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    player = relationship("Player")