from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.match import Match, MatchState
from app.models.team import Team
from app.models.player import Player, PlayerLeague, LeagueRoleEnum, PlayerTypeEnum
from app.core.dependencies import get_current_player
from app.models.feed_item import MessageTypeEnum, FeedItem
from app.services.match_validation import CONTESTATION_DELAY
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matches", tags=["matches"])

class Score(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)

@router.put("/{match_id}/start")
async def start_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
): 
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        logger.warning(f"Match {match_id}, lancé par {current_player.username} est introuvable")
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match.state != MatchState.pending:
        logger.warning(f"Le match {match_id} a déjà commencé (état actuel : {match.state})")
        raise HTTPException(status_code=400, detail=f"Le match a déjà commencé (état actuel : {match.state})")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one_or_none()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one_or_none()
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner:
        logger.warning(f"Tentative de start refusée : {current_player.username} ne contrôle aucune équipe du match {match_id}")
        raise HTTPException(status_code=400, detail="Vous ne controlez aucune de ces équipes")
    match.state = MatchState.in_progress
    await db.commit()
    await db.refresh(match)
    logger.info(f"{current_player.username} a démarré le match {match_id} ")
    return {"message": "Le match a commencé"}

@router.put("/{match_id}/score")
async def update_score(
    match_id: int,
    score: Score,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        logger.warning(f"Match {match_id}, lancé par {current_player.username} est introuvable")
        raise HTTPException(status_code=404, detail="Match introuvable")
    if match.state != MatchState.in_progress:
        logger.warning(f"Le match {match_id} n'est pas en cours (état actuel : {match.state})")
        raise HTTPException(status_code=400, detail=f"Le match n'est pas en cours (état actuel : {match.state})")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result1 = await db.execute(select(PlayerLeague).filter( PlayerLeague.league_id == match.league_id, PlayerLeague.role == LeagueRoleEnum.manager ))
    manager = result1.scalar_one_or_none()
    if manager is None:
        logger.warning(f"{current_player.username} n'est pas manager de la ligue pour le match {match_id}")
        raise HTTPException(status_code=404, detail="Manager introuvable")
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one_or_none()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one_or_none()
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner and current_player.id != manager.player_id:
        logger.warning(f"Tentative de mise à jour du score refusée : {current_player.username} ne contrôle aucune équipe du match {match_id} et n'est pas manager de la ligue")
        raise HTTPException(status_code=400, detail="Vous ne controlez aucune de ces équipes et vous n'êtes pas manager de la ligue")
    match.score_home = score.home_score
    match.score_away = score.away_score
    match.score_submitted_at = datetime.now(timezone.utc)
    match.state = MatchState.finished
    feed_item = FeedItem(
            type=MessageTypeEnum.match_event,
            match_id=match_id,
            match = match,
            league_id=match.league_id
        )
    db.add(feed_item)
    await db.commit()
    await db.refresh(match)
    await db.refresh(feed_item)
    logger.info(f"{current_player.username} a saisi le score du match {match_id} : {match.score_home}-{match.score_away}")
    minutes = int(CONTESTATION_DELAY.total_seconds() // 60)
    return {"message": f"Score enregistré, contestable pendant {minutes} minutes"}

