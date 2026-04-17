from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.player import Player, League, PlayerLeague, LeagueRoleEnum
from app.core.dependencies import get_current_player

router = APIRouter(prefix="/leagues", tags=["Leagues"])


class LeagueCreate(BaseModel):
    name: str


class LeagueResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


@router.post("/", response_model=LeagueResponse)
async def create_league(
    data: LeagueCreate,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),  # ← route protégée
):
    # Vérifie si le nom de la ligue existe déjà
    result = await db.execute(select(League).filter(League.name == data.name))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom de ligue est déjà pris")

    # Crée la ligue
    league = League(name=data.name)
    db.add(league)
    await db.commit()
    await db.refresh(league)  # ← on a besoin de league.id pour l'étape suivante

    # Ajoute le créateur comme manager automatiquement
    player_league = PlayerLeague(
        player_id=current_player.id,
        league_id=league.id,
        role=LeagueRoleEnum.manager,
    )
    db.add(player_league)
    await db.commit()

    return league


@router.get("/", response_model=list[LeagueResponse])
async def get_leagues(
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    result = await db.execute(select(League))
    return result.scalars().all()


@router.post("/{league_id}/join")
async def join_league(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    # Vérifie que la ligue existe
    result = await db.execute(select(League).filter(League.id == league_id))
    league = result.scalars().first()
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable")

    # Vérifie que le joueur n'est pas déjà dans la ligue
    result = await db.execute(
        select(PlayerLeague).filter(
            PlayerLeague.player_id == current_player.id,
            PlayerLeague.league_id == league_id,
        )
    )
    already_in = result.scalars().first()
    if already_in:
        raise HTTPException(status_code=400, detail="Tu es déjà dans cette ligue")

    # Ajoute le joueur comme membre
    player_league = PlayerLeague(
        player_id=current_player.id,
        league_id=league_id,
        role=LeagueRoleEnum.membre,
    )
    db.add(player_league)
    await db.commit()

    return {"message": f"Tu as rejoint la ligue {league.name}"}


@router.delete("/{league_id}/leave")
async def leave_league(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    # Vérifie que le joueur est dans la ligue
    result = await db.execute(
        select(PlayerLeague).filter(
            PlayerLeague.player_id == current_player.id,
            PlayerLeague.league_id == league_id,
        )
    )
    player_league = result.scalars().first()
    if not player_league:
        raise HTTPException(status_code=404, detail="Tu n'es pas dans cette ligue")

    # Un manager ne peut pas quitter sa propre ligue
    if player_league.role == LeagueRoleEnum.manager:
        raise HTTPException(status_code=400, detail="Un manager ne peut pas quitter sa ligue")

    await db.delete(player_league)
    await db.commit()

    return {"message": "Tu as quitté la ligue"}