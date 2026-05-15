from pydantic import BaseModel, Field
from datetime import datetime

class FeedItemCreate(BaseModel):
    content: str
    match_id: int | None = Field(default=None)
    league_id: int

class FeedItemResponse(BaseModel):
    id: int
    created_at: datetime
    type: str
    content: str | None = None
    player_id: int | None = None
    match_id: int| None = None

    model_config = {"from_attributes": True}