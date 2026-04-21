from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from app.database.connection import get_db
from app.models.player import Player, League, PlayerLeague, LeagueRoleEnum
from app.models.team import Team
from app.core.dependencies import get_current_player

router = APIRouter(prefix="/leagues", tags=["Leagues"])


class LeagueCreate(BaseModel):
    name: str
    max_teams: int
    max_per_player: int


class LeagueResponse(BaseModel):
    id: int
    name: str
    manager_username: str
    is_active : bool

    model_config = {"from_attributes": True}

class EquipeResponse(BaseModel):
    id: int
    nom: str
    nom_stade: str
    owner_username : str

    model_config = {"from_attributes": True}

class LigueValidateResponse(BaseModel):
    is_active : bool

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
    league = League(
        name=data.name,
        max_team=data.max_teams,
        max_per_player=data.max_per_player)
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
    result = await db.execute(select(League).options(joinedload(League.player_leagues).joinedload(PlayerLeague.player)))
    return result.unique().scalars().all()

@router.post("/{league_id}/validate", response_model=LigueValidateResponse)
async def validate_league(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    # 1. Vérifie que le joueur est bien manager de CETTE ligue
    result = await db.execute(
        select(PlayerLeague).filter(
            PlayerLeague.player_id == current_player.id,
            PlayerLeague.league_id == league_id,
            PlayerLeague.role == LeagueRoleEnum.manager,
        )
    )
    manager = result.scalars().first()
    if not manager:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas manager de cette ligue")

    # 2. Récupère la ligue
    result = await db.execute(select(League).filter(League.id == league_id))
    league = result.scalars().first()
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable")

    # 3. Active la ligue
    league.is_active = True
    await db.commit()
    await db.refresh(league)

    return league

@router.get("/{league_id}/teams", response_model=list[EquipeResponse])
async def get_teams(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    result = await db.execute(select(Team).options(joinedload(Team.owner)).where(Team.id_league == league_id))
    teams = result.unique().scalars().all()
    return teams

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