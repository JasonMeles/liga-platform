from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerResponse

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

@router.post("/", response_model=PlayerResponse)
async def create_player(player: PlayerCreate, db: AsyncSession = Depends(get_db)):
    db_player = Player(
        username=player.username,
        email=player.email
    )
    db.add(db_player)
    await db.commit()
    await db.refresh(db_player)
    return db_player

@router.get("/", response_model=list[PlayerResponse])
async def get_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player))
    players = result.scalars().all()
    return players

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    return player

@router.delete("/{player_id}")
async def delete_player(player_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    await db.delete(player)
    await db.commit()
    return {"message": f"Joueur {player_id} supprimé"}