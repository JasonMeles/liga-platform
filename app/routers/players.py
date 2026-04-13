from fastapi import APIRouter
from app.schemas.player import PlayerCreate

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

players_db = []

@router.post("/")
async def create_player(player: PlayerCreate):
    players_db.append(player.model_dump())
    return {"message": "Joueur créé avec succès", "player": player}

@router.get("/")
async def get_players():
    return {"players": players_db}