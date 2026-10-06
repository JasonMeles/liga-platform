import secrets

from app.models.player import League
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans 0, O, 1, I

def generer_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))

async def generer_code_unique(db: AsyncSession) -> str:
    code = generer_code()
    while await db.scalar(select(League.id).filter_by(invite_code=code)):
        code = generer_code()
    return code