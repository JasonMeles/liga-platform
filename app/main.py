from fastapi import FastAPI
from app.routers import players, auth, leagues, teams
from contextlib import asynccontextmanager
from app.database.connection import get_db
from app.models.player import Player, PlayerTypeEnum
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée l'utilisateur IA au démarrage s'il n'existe pas
    async for db in get_db():
        result = await db.execute(select(Player).filter(Player.username == "AI"))
        ai = result.scalars().first()
        if not ai:
            ai_player = Player(
                username="AI",
                email="ai@liga-platform.com",
                hashed_password="",
                player_type=PlayerTypeEnum.ia
            )
            db.add(ai_player)
            await db.commit()
    yield


app = FastAPI(
    title="Liga Platform API",
    description="Backend pour la gestion de ligues gaming",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(players.router) 
app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(teams.router)


@app.get("/")
async def root():
    return {"message": "Liga Platform is alive 🎮"}

@app.get("/health")
async def health():
    return {"status": "ok"}

