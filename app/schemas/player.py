from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.player import LeagueRoleEnum

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr

class LeagueMembershipPublic(BaseModel):
    name: str
    joined_at: datetime
    model_config = {"from_attributes": True}


class LeagueMembershipPrivate(BaseModel):
    name: str
    role: LeagueRoleEnum
    joined_at: datetime
    model_config = {"from_attributes": True}

class PlayerResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    player_leagues: list[LeagueMembershipPublic]
    model_config = {"from_attributes": True}

class PlayerMe(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    player_leagues: list[LeagueMembershipPrivate]
    model_config = {"from_attributes": True}