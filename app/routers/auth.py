from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from app.database.connection import get_db
from app.models.player import Player, RefreshToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str        # ← ajouté
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str        # ← le token envoyé par le client


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Vérifie si le username existe déjà
    result = await db.execute(select(Player).filter(Player.username == data.username))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Username déjà pris")

    # Crée le joueur
    player = Player(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(player)
    await db.commit()
    await db.refresh(player)

    # Génère les deux tokens
    access_token = create_access_token({"sub": player.username})
    refresh_token_value, expires_at = create_refresh_token()

    # Stocke le refresh token en base
    refresh_token = RefreshToken(
        token=refresh_token_value,
        player_id=player.id,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Vérifie les identifiants
    result = await db.execute(select(Player).filter(Player.username == form_data.username))
    player = result.scalars().first()
    if not player or not verify_password(form_data.password, player.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    # Supprime les anciens refresh tokens de ce joueur (bonne hygiène)
    old_tokens = await db.execute(
        select(RefreshToken).filter(RefreshToken.player_id == player.id)
    )
    for old_token in old_tokens.scalars().all():
        await db.delete(old_token)

    # Génère les deux nouveaux tokens
    access_token = create_access_token({"sub": player.username})
    refresh_token_value, expires_at = create_refresh_token()

    # Stocke le nouveau refresh token en base
    refresh_token = RefreshToken(
        token=refresh_token_value,
        player_id=player.id,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    # Cherche le refresh token en base
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token == data.refresh_token)
    )
    stored_token = result.scalars().first()

    # Token introuvable ou expiré
    if not stored_token:
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    if stored_token.expires_at < datetime.now(timezone.utc):
        await db.delete(stored_token)
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    # Récupère le joueur associé
    result = await db.execute(
        select(Player).filter(Player.id == stored_token.player_id)
    )
    player = result.scalars().first()

    # Rotation — supprime l'ancien, crée un nouveau
    await db.delete(stored_token)

    access_token = create_access_token({"sub": player.username})
    new_refresh_value, new_expires_at = create_refresh_token()

    new_refresh_token = RefreshToken(
        token=new_refresh_value,
        player_id=player.id,
        expires_at=new_expires_at,
    )
    db.add(new_refresh_token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_value,
    )


@router.post("/logout")
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    # Cherche et supprime le refresh token
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.token == data.refresh_token)
    )
    stored_token = result.scalars().first()
    if stored_token:
        await db.delete(stored_token)
        await db.commit()

    # Toujours retourner 200 — ne pas révéler si le token existait
    return {"message": "Déconnecté avec succès"}