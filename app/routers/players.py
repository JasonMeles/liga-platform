from fastapi import APIRouter
from app.schemas.player import PlayerCreate
from fastapi import APIRouter, HTTPException

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

@router.get("/{player_id}")
async def get_player(player_id: int):
    if player_id < 0 or player_id >= len(players_db):
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    return {"player": players_db[player_id]}

@router.delete("/{player_id}")
async def delete_player(player_id: int):
    if player_id < 0 or player_id >= len(players_db):
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    deleted_player = players_db[player_id]["username"]
    players_db.pop(player_id)
    return {"message": f"Joueur {deleted_player} a été supprimé"}

@router.put("/{player_id}")
async def update_player(player_id: int, player: PlayerCreate):
    if player_id < 0 or player_id >= len(players_db):
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    old_username = players_db[player_id]["username"]
    players_db[player_id] = player.model_dump()
    return {"message": f"Joueur {old_username} mis à jour", "player": players_db[player_id]}