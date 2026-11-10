from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.database.connection import get_db
from app.models.match import Match, MatchState
from app.models.team import Team
from app.models.player import Player, PlayerLeague, LeagueRoleEnum, SportTypeEnum, League, PlayerTypeEnum
from app.core.dependencies import get_current_player
from app.models.feed_item import MessageTypeEnum, FeedItem
from app.services.match_validation import CONTESTATION_DELAY, est_contestable
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import logging
import random

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
            league_id=match.league_id,
            content=f"{team_home.nom} {match.score_home} - {match.score_away} {team_away.nom}"
        )
    db.add(feed_item)
    await db.commit()
    await db.refresh(match)
    await db.refresh(feed_item)
    logger.info(f"{current_player.username} a saisi le score du match {match_id} : {match.score_home}-{match.score_away}")
    minutes = int(CONTESTATION_DELAY.total_seconds() // 60)
    return {"message": f"Score enregistré, contestable pendant {minutes} minutes"}

@router.put("/{match_id}/simulate")
async def simulate_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    # --- Bloc 1 : le match existe ? ---
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        logger.warning(f"Simulation : match {match_id} introuvable (demandé par {current_player.username})")
        raise HTTPException(status_code=404, detail="Match introuvable")

    # --- Bloc 2 : le match peut-il encore être simulé ? (anti-relance) ---
    if match.state not in (MatchState.pending, MatchState.in_progress):
        logger.warning(f"Simulation refusée : match {match_id} déjà joué (état : {match.state})")
        raise HTTPException(status_code=400, detail=f"Ce match ne peut plus être simulé (état actuel : {match.state})")

    # --- Bloc 3 : charger la ligue et les équipes AVEC leur propriétaire ---
    result = await db.execute(select(League).where(League.id == match.league_id))
    league = result.scalar_one()

    result = await db.execute(select(Team).options(joinedload(Team.owner)).where(Team.id == match.team_home_id))
    team_home = result.scalar_one()
    result = await db.execute(select(Team).options(joinedload(Team.owner)).where(Team.id == match.team_away_id))
    team_away = result.scalar_one()

    home_ia = team_home.owner.player_type == PlayerTypeEnum.ia
    away_ia = team_away.owner.player_type == PlayerTypeEnum.ia

    # --- Bloc 4 : qui a le droit de simuler ? ---
    contestable = False
    if home_ia and away_ia:
        # IA vs IA → seul le manager
        result = await db.execute(select(PlayerLeague).where(
            PlayerLeague.league_id == match.league_id,
            PlayerLeague.role == LeagueRoleEnum.manager,
        ))
        manager = result.scalar_one_or_none()
        autorise = manager is not None and manager.player_id == current_player.id
    elif home_ia or away_ia:
        # Humain vs IA → seul le propriétaire humain
        equipe_humaine = team_away if home_ia else team_home
        autorise = current_player.id == equipe_humaine.id_owner
    elif team_home.id_owner == team_away.id_owner:
        # Même propriétaire → ce propriétaire
        autorise = current_player.id == team_home.id_owner
    else:
        # Deux humains différents → l'un des deux, et le score sera contestable
        autorise = current_player.id in (team_home.id_owner, team_away.id_owner)
        contestable = True

    if not autorise:
        logger.warning(f"Simulation refusée : {current_player.username} n'a pas le droit de simuler le match {match_id}")
        raise HTTPException(status_code=403, detail="Vous n'avez pas le droit de simuler ce match")

    # --- Bloc 5 : tirer le score selon le sport ---
    if league.sport_type == SportTypeEnum.football:
        match.score_home = random.randint(0, 5)
        match.score_away = random.randint(0, 5)
    elif league.sport_type == SportTypeEnum.basketball:
        match.score_home = random.randint(70, 120)
        match.score_away = random.randint(70, 120)
        if match.score_home == match.score_away:
            # Pas d'égalité au basket : +1 à une équipe au hasard
            if random.choice(["home", "away"]) == "home":
                match.score_home += 1
            else:
                match.score_away += 1

    # --- Bloc 6 : terminer le match, feed, commit ---
    match.state = MatchState.finished
    match.score_submitted_at = datetime.now(timezone.utc) if contestable else None

    feed_item = FeedItem(
        type=MessageTypeEnum.match_event,
        match_id=match_id,
        match=match,
        league_id=match.league_id,
        content=f"{team_home.nom} {match.score_home} - {match.score_away} {team_away.nom}"
    )
    db.add(feed_item)
    await db.commit()
    await db.refresh(match)

    logger.info(f"{current_player.username} a simulé le match {match_id} : {match.score_home}-{match.score_away}")
    if contestable:
        minutes = int(CONTESTATION_DELAY.total_seconds() // 60)
        return {"message": f"Score simulé, contestable pendant {minutes} minutes"}
    return {"message": "Score simulé et validé"}

@router.put("/{match_id}/contest")
async def contest_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        logger.warning(f"Contest : match {match_id} introuvable (demandé par {current_player.username})")
        raise HTTPException(status_code=404, detail="Match introuvable")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one()
    if current_player.id != team_away.id_owner and current_player.id != team_home.id_owner:
        logger.warning(f"Tentative de contestation refusée : {current_player.username} ne contrôle aucune équipe du match {match_id}")
        raise HTTPException(status_code=403, detail="Vous ne controlez aucune de ces équipes")
    if not est_contestable(match):
        logger.warning(f"Contest refusé : match {match_id} non contestable (état : {match.state})")
        raise HTTPException(status_code=400, detail=f"Ce match n'est pas contestable (état actuel : {match.state})")
    # Le score reste tel quel, mais le match passe en attente de réponse du manager
    match.state = MatchState.contested
    feed_item = FeedItem(
            type=MessageTypeEnum.match_event,
            match_id=match_id,
            match=match,
            league_id=match.league_id,
            content=f"Le score du match {team_home.nom} {match.score_home} - {match.score_away} {team_away.nom} a été contesté par {current_player.username}"
        )
    db.add(feed_item)
    await db.commit()
    await db.refresh(match)
    logger.info(f"{current_player.username} a contesté le score du match {match_id}")
    return {"message": "Le score a été contesté et le match est de nouveau en attente"}

@router.put("/{match_id}/resolve")
async def resolve_contestation(
    match_id: int,
    score: Score,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player)
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if match is None:
        logger.warning(f"Resolve : match {match_id} introuvable (demandé par {current_player.username})")
        raise HTTPException(status_code=404, detail="Match introuvable")
    id_home = match.team_home_id
    id_away = match.team_away_id
    result2 =  await db.execute(select(Team).where(Team.id == id_home))
    team_home = result2.scalar_one()
    result3 = await db.execute(select(Team).where(Team.id == id_away))
    team_away = result3.scalar_one()
    result1 = await db.execute(select(PlayerLeague).filter( PlayerLeague.league_id == match.league_id, PlayerLeague.role == LeagueRoleEnum.manager ))
    manager = result1.scalar_one_or_none()
    if manager is None or manager.player_id != current_player.id:
        logger.warning(f"Tentative de résolution de contestation refusée : {current_player.username} n'est pas manager de la ligue pour le match {match_id}")
        raise HTTPException(status_code=403, detail="Vous n'êtes pas manager de la ligue pour ce match")
    if match.state != MatchState.contested:
        logger.warning(f"Resolve refusé : match {match_id} non contesté (état : {match.state})")
        raise HTTPException(status_code=400, detail=f"Ce match n'est pas contesté (état actuel : {match.state})")
    
    #Enreistrer le score entré par le manager, et mettre le match en terminé
    match.score_home = score.home_score
    match.score_away = score.away_score
    match.score_submitted_at = None
    match.state = MatchState.finished
    feed_item = FeedItem(
            type=MessageTypeEnum.match_event,
            match_id=match_id,
            match=match,
            league_id=match.league_id,
            content=f"La contestation du score du match a été résolue par le manager {current_player.username}, le score final du match {team_home.nom} - {team_away.nom} est {match.score_home} - {match.score_away}"
        )
    db.add(feed_item)
    await db.commit()
    await db.refresh(feed_item)
    await db.refresh(match)
    logger.info(f"{current_player.username} a résolu la contestation du score du match {match_id}")
    return {"message": "La contestation a été résolue et le match est terminé"}