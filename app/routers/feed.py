from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.team import Team
from app.models.player import Player, League, PlayerLeague
from app.models.feed_item import MessageTypeEnum, FeedItem
from app.schemas.feed_item import FeedItemCreate
from app.models.match import Match
from app.core.dependencies import get_current_player
from pydantic import BaseModel
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/feed", tags=["Feed"])

@router.post("/")
async def create_feed_item(
    feed_item: FeedItemCreate,
    current_player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db)
):
    
    match_official : Match = None
    # Vérifier que le match existe si un match_id est fourni
    if feed_item.match_id is not None:
        result = await db.execute(select(Match).where(Match.id == feed_item.match_id))
        match_official = result.scalar_one_or_none()
        if match_official is None:
            raise HTTPException(status_code=404, detail="Match introuvable")
        league_id = match_official.league_id
        # Vérifier que le joueur appartient à la ligue du match
        result = await db.execute(select(PlayerLeague).filter(PlayerLeague.player_id == current_player.id, PlayerLeague.league_id == league_id))
        player = result.scalar_one_or_none()
        if player is None:
            raise HTTPException(status_code=404, detail="Joueur introuvable")
    
    # vérifier que le joueur appartient à la ligue
    result = await db.execute(select(PlayerLeague).filter(PlayerLeague.player_id == current_player.id, PlayerLeague.league_id == feed_item.league_id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")   

    #créer le feed item
    feed_item = FeedItem(
        type=MessageTypeEnum.comment,
        content=feed_item.content,
        player_id=current_player.id,
        match_id=feed_item.match_id,
        player = current_player,
        match = match_official,
        league_id=feed_item.league_id
    )
    db.add(feed_item)
    await db.commit()
    await db.refresh(feed_item)
    return feed_item

@router.get("/league/{league_id}")
async def get_feed_items_for_league(
    league_id: int,
    current_player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier que le joueur appartient à la ligue
    result = await db.execute(select(PlayerLeague).filter(PlayerLeague.player_id == current_player.id, PlayerLeague.league_id == league_id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    # Récupérer les feed items de la ligue
    result = await db.execute(
        select(FeedItem)
        .options(
            joinedload(FeedItem.player),
            joinedload(FeedItem.match).joinedload(Match.team_home),
            joinedload(FeedItem.match).joinedload(Match.team_away),
        )
        .filter(FeedItem.league_id == league_id)
        .order_by(FeedItem.created_at.desc())
    )
    feed_items = result.scalars().all()

    message_list = [
        {
            "username": message.player.username if message.player else None,
            "content": message.content,
            "type": message.type,
            "created_at": message.created_at,
            "match": {
                "id": message.match.id,
                "team_home": message.match.team_home.nom,
                "score_home": message.match.score_home,
                "team_away": message.match.team_away.nom,
                "score_away": message.match.score_away,
            } if message.match else None,
        }
        for message in feed_items
    ]

    return message_list