from fastapi import FastAPI
from app.routers import players

app = FastAPI(
    title="Liga Platform API",
    description="Backend pour la gestion de ligues gaming",
    version="0.1.0",
)

app.include_router(players.router) 

@app.get("/")
async def root():
    return {"message": "Liga Platform is alive 🎮"}

@app.get("/health")
async def health():
    return {"status": "ok"}