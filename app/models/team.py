from sqlalchemy.sql import func
from app.database.connection import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
import enum

class Team(Base):
    __tablename__ = "equipes"
    __table_args__ = (UniqueConstraint("nom", "id_league"),)

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    nom_stade= Column(String, nullable=False)
    id_owner= Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    id_league= Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    