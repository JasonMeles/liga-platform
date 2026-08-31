from app.core import logging_config
from app.routers import auth, feed, leagues, matches, players, teams
from fastapi import FastAPI
from app.routers import websockets
from contextlib import asynccontextmanager
from app.database.connection import get_db
from app.models.player import Player, PlayerTypeEnum
from sqlalchemy import select
from fastapi import Request
from fastapi.responses import JSONResponse
import logging


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

logging_config.setup_logging()

app = FastAPI(
    title="Liga Platform API",
    description="Backend pour la gestion de ligues gaming",
    version="0.1.0",
    lifespan=lifespan
)

logger = logging.getLogger(__name__)

app.include_router(players.router) 
app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(feed.router)
app.include_router(websockets.router)

@app.get("/")
async def root():
    return {"message": "Liga Platform is alive 🎮"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée sur {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue"}
    )
