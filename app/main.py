from fastapi import FastAPI
from app.routers import players, auth
from app.routers import players, auth, leagues

app = FastAPI(
    title="Liga Platform API",
    description="Backend pour la gestion de ligues gaming",
    version="0.1.0",
)

app.include_router(players.router) 
app.include_router(auth.router)
app.include_router(leagues.router)

@app.get("/")
async def root():
    return {"message": "Liga Platform is alive 🎮"}

@app.get("/health")
async def health():
    return {"status": "ok"}

