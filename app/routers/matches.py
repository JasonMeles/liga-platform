from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.match import Match, MatchState
from app.models.team import Team
from app.models.player import Player, PlayerLeague, LeagueRoleEnum, PlayerTypeEnum
from app.core.dependencies import get_current_player

router = APIRouter(prefix="/matches", tags=["matches"])

@router.put("/{match_id}/start")
async def start_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
): 
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match.state != MatchState.pending:
        raise HTTPException(status_code=400, detail=f"Le match a déjà commencé (état actuel : {match.state})")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one_or_none()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one_or_none()
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner:
        raise HTTPException(status_code=400, detail="Vous ne controlez aucune de ces équipes")
    match.state = MatchState.in_progress
    await db.commit()
    await db.refresh(match)
    return {"message": "Le match a commencé"}

@router.put("/{match_id}/score")
async def update_score(
    match_id: int,
    home_score: int,
    away_score: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match.state != MatchState.in_progress:
        raise HTTPException(status_code=400, detail=f"Le match n'est pas en cours (état actuel : {match.state})")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result1 = await db.execute(select(PlayerLeague).filter( PlayerLeague.league_id == match.league_id, PlayerLeague.role == LeagueRoleEnum.manager ))
    manager = result1.scalar_one_or_none()
    if manager is None:
        raise HTTPException(status_code=404, detail="Manager introuvable")
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one_or_none()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one_or_none()
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner and current_player.id != manager.player_id:
        raise HTTPException(status_code=400, detail="Vous ne controlez aucune de ces équipes et vous n'êtes pas manager de la ligue")
    match.score_home = home_score
    match.score_away = away_score
    await db.commit()
    await db.refresh(match)
    return {"message": "Score mis à jour"}

@router.put("/{match_id}/finish")
async def finish_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match.state != MatchState.in_progress:
        raise HTTPException(status_code=400, detail=f"Le match n'est pas en cours (état actuel : {match.state})")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result1 = await db.execute(select(PlayerLeague).filter( PlayerLeague.league_id == match.league_id, PlayerLeague.role == LeagueRoleEnum.manager ))
    manager = result1.scalar_one_or_none()
    if manager is None:
        raise HTTPException(status_code=404, detail="Manager introuvable")
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one_or_none()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one_or_none()
    if team_home.id_owner is None and team_away.id_owner is None and current_player.id != manager.player_id:
        raise HTTPException(status_code=400, detail="Vous n'êtes pas manager de la ligue")
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner:
        raise HTTPException(status_code=400, detail="Vous ne controlez aucune de ces équipes")
    match.state = MatchState.finished
    await db.commit()
    await db.refresh(match)
    return {"message": "Le match est terminé"}