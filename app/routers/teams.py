from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db
from app.models.team import Team
from app.models.player import Player, League, PlayerLeague, LeagueRoleEnum
from app.core.dependencies import get_current_player
from pydantic import BaseModel

router = APIRouter(prefix="/teams", tags=["Teams"])

class EquipeCreate(BaseModel):
    nom: str
    nom_stade: str
    id_league: int
    is_ia: bool = False

class EquipeResponse(BaseModel):
    id: int
    nom: str
    nom_stade: str
    owner_username: str

    model_config = {"from_attributes": True}

class EquipeUpdate(BaseModel):
    nom_stade: str


@router.post("/", response_model=EquipeResponse)
async def create_team(
    data: EquipeCreate,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),  # ← route protégée
):
    # Vérifie si le nom de l'équipe existe déjà
    result = await db.execute(select(Team).filter(Team.nom == data.nom, Team.id_league == data.id_league))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce nom d'équipe est déjà pris")

    # Détermine le propriétaire
    if data.is_ia:
        # Vérifie que le joueur est manager de cette ligue
        result_membership = await db.execute(
            select(PlayerLeague).filter(
                PlayerLeague.player_id == current_player.id,
                PlayerLeague.league_id == data.id_league,
                PlayerLeague.role == LeagueRoleEnum.manager
            )
        )
        if not result_membership.scalars().first():
            raise HTTPException(status_code=403, detail="Seul le manager peut créer une équipe IA")
        result_ai = await db.execute(select(Player).filter(Player.username == "AI"))
        owner_id = result_ai.scalars().first().id
    else:
        owner_id = current_player.id

    # Crée l'équipe
    equipe = Team(
        nom=data.nom,
        nom_stade = data.nom_stade,
        id_league = data.id_league,
        id_owner = current_player.id)
    db.add(equipe)
    await db.commit()
    await db.refresh(equipe)  # ← on a besoin de equipe.id pour plus tard
    return {
        "id": equipe.id,
        "nom": equipe.nom,
        "nom_stade": equipe.nom_stade,
        "owner_username": "AI" if data.is_ia else current_player.username
        }

@router.post("/{team_id}/claim")
async def assign_team(team_id: int, db: AsyncSession = Depends(get_db), current_player: Player =Depends(get_current_player)):
    # 1. Récupère l'équipe
    result = await db.execute(select(Team).where(Team.id == team_id))
    equipe = result.scalar_one_or_none()
    if equipe is None:
        raise HTTPException(status_code=404, detail="Equipe introuvable")

    # 2. Vérifie que l'équipe est bien contrôlée par l'IA
    result_ai = await db.execute(select(Player).filter(Player.username == "AI"))
    ai = result_ai.scalars().first()
    if equipe.id_owner != ai.id:
        raise HTTPException(status_code=403, detail="Cette équipe n'est pas une équipe IA")

    # 3. Vérifie que le joueur est membre de la ligue
    result_membership = await db.execute(
        select(PlayerLeague).filter(
            PlayerLeague.player_id == current_player.id,
            PlayerLeague.league_id == equipe.id_league
        )
    )
    membership = result_membership.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Tu ne fais pas partie de cette ligue")

    # 4. Vérifie le max d'équipes autorisées
    result_league = await db.execute(select(League).filter(League.id == equipe.id_league))
    league = result_league.scalars().first()

    result_count = await db.execute(
        select(Team).filter(
            Team.id_owner == current_player.id,
            Team.id_league == equipe.id_league
        )
    )
    teams_owned = result_count.scalars().all()
    if len(teams_owned) >= league.max_per_player:
        raise HTTPException(status_code=403, detail="Nombre maximum d'équipes atteint")

    # Revendique l'équipe
    equipe.id_owner = current_player.id
    await db.commit()
    await db.refresh(equipe)
    return {"message": f"Equipe {equipe.nom} revendiquée avec succès"}

@router.get("/{team_id}")
async def get_profil(team_id: int,
    db: AsyncSession = Depends(get_db),
    current_player: Player = Depends(get_current_player),):
    result = await db.execute(
    select(Team, Player)
    .join(Player, Player.id == Team.id_owner)
    .where(Team.id == team_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Equipe introuvable")
    equipe, owner = row
    return {
        "id": equipe.id,
        "nom": equipe.nom,
        "nom_stade": equipe.nom_stade,
        "owner_username": owner.username
    }


@router.put("/{team_id}")
async def modify_team(team_id: int, data: EquipeUpdate, db: AsyncSession = Depends(get_db), current_player: Player =Depends(get_current_player)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    equipe = result.scalar_one_or_none()
    if equipe is None:
        raise HTTPException(status_code=404, detail="Equipe introuvable")
    if equipe.id_owner != current_player.id:
        raise HTTPException(status_code=403, detail="N'est le propriétaire de l'équipe")
    equipe.nom_stade = data.nom_stade
    await db.commit()
    await db.refresh(equipe)
    return {"message": f"Equipe {team_id} modifié"} #affiche le nom de l'équipe modifié

@router.delete("/{team_id}")
async def delete_team(team_id: int, db: AsyncSession = Depends(get_db), current_player: Player =Depends(get_current_player)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    equipe = result.scalar_one_or_none()
    if equipe is None:
        raise HTTPException(status_code=404, detail="Equipe introuvable")
    if equipe.id_owner != current_player.id:
        raise HTTPException(status_code=403, detail="N'est le propriétaire de l'équipe")
    await db.delete(equipe)
    await db.commit()
    return {"message": f"Equipe {team_id} supprimé"} #affiche le nom de l'équipe supprimé




