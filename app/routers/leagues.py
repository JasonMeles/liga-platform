from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from app.database.connection import get_db
from app.models.player import Player, League, PlayerLeague, LeagueRoleEnum, SportTypeEnum
from app.models.team import Team
from app.core.dependencies import get_current_player
from app.models.match import Match
from app.models.team import Team
from app.services.match_generator import generate_matches
from sqlalchemy import or_
from app.models.match import Match, MatchState

router = APIRouter(prefix="/leagues", tags=["Leagues"])


class LeagueCreate(BaseModel):
    name: str
    max_teams: int
    max_per_player: int
    total_journeys: int


class LeagueResponse(BaseModel):
    id: int
    name: str
    manager_username: str
    is_active : bool
    total_journeys : int

    model_config = {"from_attributes": True}

class EquipeResponse(BaseModel):
    id: int
    nom: str
    nom_stade: str
    owner_username : str
    journeys_remaining: int

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
        max_per_player=data.max_per_player,
        total_journeys=data.total_journeys)
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

    return {
    "id": league.id,
    "name": league.name,
    "manager_username": current_player.username,
    "is_active": league.is_active
    }


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
    if league.is_active:
        raise HTTPException(status_code=400, detail="Cette ligue est déjà validée")
    
        # 3. Récupère les équipes de la ligue
    result = await db.execute(
        select(Team).filter(Team.id_league == league_id)
    )
    equipes = result.scalars().all()

    if len(equipes) < 2:
        raise HTTPException(status_code=400, detail="La ligue doit avoir au moins 2 équipes")

    # 4. Génère les matchs
    matchs = generate_matches(list(equipes), league.total_journeys)
    for match in matchs:
        db.add(match)

    # 5. Active la ligue
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
    result = await db.execute(select(League).filter(League.id == league_id))
    league = result.scalars().first()
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable")

    result = await db.execute(
        select(Team).options(joinedload(Team.owner)).where(Team.id_league == league_id)
    )
    teams = result.unique().scalars().all()

    response = []
    for team in teams:
        result_matches = await db.execute(
            select(Match).filter(
                or_(Match.team_home_id == team.id, Match.team_away_id == team.id),
                Match.state == MatchState.finished
            )
        )
        matches_joues = len(result_matches.scalars().all())
        response.append({
            "id": team.id,
            "nom": team.nom,
            "nom_stade": team.nom_stade,
            "owner_username": team.owner_username,
            "journeys_remaining": league.total_journeys - matches_joues
        })

    return response

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

@router.get("/{league_id}/calendar")
async def show_calendar(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    # Vérifie que la ligue existe
    result = await db.execute(select(League).filter(League.id == league_id))
    league = result.scalars().first()
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable")

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

    result = await db.execute(
        select(Match).options(joinedload(Match.team_home), joinedload(Match.team_away)).filter(Match.league_id == league_id)
    )
    matches = result.scalars().all()
    matches = [
            {
                "id": match.id,
                "team_home": match.team_home.nom,
                "team_away": match.team_away.nom,
                "score_home": match.score_home,
                "score_away": match.score_away,
                "state": match.state,
                "scheduled_at": match.scheduled_at,
                "stadium": match.team_home.nom_stade,
                "round_number": match.round_number
            }
            for match in matches]

    return matches

@router.get("/{league_id}/standings")
async def show_standings(
    league_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),
):
    # Vérifie que la ligue existe
    result = await db.execute(select(League).filter(League.id == league_id))
    league = result.scalars().first()
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable")

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

    result = await db.execute(
        select(Team).options(joinedload(Team.owner)).where(Team.id_league == league_id)
    )
    teams = result.unique().scalars().all()

    if league.sport_type == SportTypeEnum.football:
        standings = []
        for team in teams:
            result_matches = await db.execute(
                select(Match).filter(
                    or_(Match.team_home_id == team.id, Match.team_away_id == team.id),
                    Match.state == MatchState.finished
                )
            )
            matches_joues = result_matches.scalars().all()
            points = 0
            goals_for = 0
            goals_against = 0
            for match in matches_joues:
                if match.team_home_id == team.id:
                    if match.score_home > match.score_away:
                        points += 3
                    elif match.score_home == match.score_away:
                        points += 1
                else:
                    if match.score_away > match.score_home:
                        points += 3
                    elif match.score_away == match.score_home:
                        points += 1
                goals_for += match.score_home if match.team_home_id == team.id else match.score_away
                goals_against += match.score_away if match.team_home_id == team.id else match.score_home

            standings.append({
                "team": team.nom,
                "owner": team.owner_username,
                "points": points,
                "matches_played": len(matches_joues),
                "goals_for": goals_for,
                "goals_against": goals_against
            })

        standings.sort(key=lambda x: (x["points"], x["goals_for"] - x["goals_against"]), reverse=True)

    else : # basketball
        standings = []
        for team in teams:
            result_matches = await db.execute(
                select(Match).filter(
                    or_(Match.team_home_id == team.id, Match.team_away_id == team.id),
                    Match.state == MatchState.finished
                )
            )
            matches_joues = result_matches.scalars().all()
            wins = 0
            losses = 0
            points_for = 0
            points_against = 0
            for match in matches_joues:
                if match.team_home_id == team.id and match.score_home > match.score_away:
                    wins += 1
                elif match.team_away_id == team.id and match.score_away > match.score_home:
                    wins += 1
                else:
                    losses += 1
                points_for += match.score_home if match.team_home_id == team.id else match.score_away
                points_against += match.score_away if match.team_home_id == team.id else match.score_home

            standings.append({
                "team": team.nom,
                "owner": team.owner_username,
                "wins": wins,
                "losses": losses,
                "points_for": points_for,
                "points_against": points_against,
                "matches_played": len(matches_joues)
            })

        standings.sort(key=lambda x: (x["wins"], x["points_for"] - x["points_against"]), reverse=True)

    return standings