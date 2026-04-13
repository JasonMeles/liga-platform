from fastapi import FastAPI

app = FastAPI(
    title="Liga Platform API",
    description="Backend pour la gestion de ligues gaming",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Liga Platform is alive 🎮"}

@app.get("/health")
async def health():
    return {"status": "ok"}