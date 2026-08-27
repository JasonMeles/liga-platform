from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.player import Player, PlayerLeague
from app.schemas.player import PlayerCreate, PlayerResponse, PlayerMe
from app.core.dependencies import get_current_player
from sqlalchemy.orm import joinedload

router = APIRouter(
    prefix="/players",
    tags=["players"]
)



@router.get("/", response_model=list[PlayerResponse])
async def get_players(db: AsyncSession = Depends(get_db)):
    result = (await db.execute(select(Player).options(joinedload(Player.player_leagues).joinedload(PlayerLeague.league)))).unique()
    players = result.scalars().all()
    return players

@router.get("/profil", response_model=PlayerMe)
async def get_profil(current_player: Player = Depends(get_current_player), db: AsyncSession = Depends(get_db)):
    result = (await db.execute(select(Player).where(Player.id == current_player.id).options(joinedload(Player.player_leagues).joinedload(PlayerLeague.league)))).unique()
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    return player


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    result = (await db.execute(select(Player).where(Player.id == player_id).options(joinedload(Player.player_leagues).joinedload(PlayerLeague.league)))).unique()
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


